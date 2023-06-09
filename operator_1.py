import subprocess
import queue
from sys import flags
import threading
import tempfile
from .utils import *
from .pack_context import *
from .connection import *
from .os_iface import *
from .island_params import *
from .register_utils import check_engine, unregister_engine
from .overlay import EngineOverlayManager
from .prefs_scripted_utils import ScriptParams, SCRIPTED_PIPELINE_DIRNAME, ENGINE_PACKAGES_DIRNAME
from .log import LogManager
from .event import DefaultFinishConditionMixin 
from .out_island import OutIslands 
import bmesh
import bpy
from bpy.props import IntProperty, FloatProperty, BoolProperty, StringProperty, EnumProperty, CollectionProperty, PointerProperty
import mathutils

class NoUvFaceError(Exception):
    pass

class ModeIdAttributeMixin:

    mode_id : StringProperty(name='mode_id', default='')

class DHPM_OT_Generic(bpy.types.Operator):
    
    pass

class DHPM_OT_Engine(DHPM_OT_Generic, DefaultFinishConditionMixin):

    bl_options = {'UNDO'}

    MODAL_INTERVAL_S = 0.1
    STATUS_INITIAL = 'Initialization'
    HINT_INITIAL = 'press ESC to cancel'

    interactive = False

    @classmethod
    def poll(cls, context):
        prefs = get_prefs()
        return prefs.engine_initialized and context.active_object is not None and context.active_object.mode == 'EDIT'

    def __init__(self):
        
        self.cancel_sig_sent = False
        self._timer = None

    def check_engine_retcode(self, retcode):
        if retcode in {DhpmRetCode.SUCCESS,
                       DhpmRetCode.INVALID_ISLANDS,
                       DhpmRetCode.NO_SPACE,
                       DhpmRetCode.NO_SIUTABLE_DEVICE,
                       DhpmRetCode.INVALID_INPUT,
                       DhpmRetCode.WARNING}:
            return

        if retcode == DhpmRetCode.CANCELLED:
            self.log_manager.log(DhpmLogType.STATUS, 'Operation cancelled by the user')
            return

        raise RuntimeError('Engine process returned an error')

    def get_scenario_id(self):

        if hasattr(self, 'SCENARIO_ID'):
            return self.SCENARIO_ID

        if self.mode is not None and hasattr(self.mode, 'SCENARIO_ID'):
            return self.mode.SCENARIO_ID

        raise RuntimeError("Provide a 'get_senario_id' method")

    def get_scenario(self, scenario_id):

        scenario = RunScenario.get_scenario(scenario_id)

        if scenario is None:
            raise RuntimeError('Invalid scenario id provided')

        return scenario

    def mode_method_std_call(self, default_impl, method_name):

        if self.mode is not None and hasattr(self.mode, method_name):
            method = getattr(self.mode, method_name)
            return method()

        return default_impl()

    def raiseUnexpectedOutputError(self):

        raise RuntimeError('Unexpected output from the pack process')

    def set_report(self, report_type, report_str):

        if self.isolated_execution() and report_type != 'ERROR':
            return

        self.report({report_type}, report_str)

    def add_warning(self, warn_msg):
        pass

    def get_box_renderer(self):

        return self.mode_method_std_call(lambda: None, 'get_box_renderer')

    def get_iparam_serializers(self):

        return self.mode_method_std_call(lambda: [], 'get_iparam_serializers')

    def get_group_sparam_handler(self):

        return self.mode_method_std_call(lambda: None, 'get_group_sparam_handler')

    def update_context_meshes(self):
        if self.p_context is not None:
            self.p_context.update_meshes()
            self.redraw_context_area()

    def exit_common(self):

        if self.p_context is not None:
            if self._timer is not None:
                wm = self.p_context.context.window_manager
                wm.event_timer_remove(self._timer)

        if self.ov_manager is not None:
            self.ov_manager.finish()

        if self.box_renderer is not None:
            self.box_renderer.finish()

        if self.show_region_hud_saved is not None:
            self.context.area.spaces.active.show_region_hud = self.show_region_hud_saved

        self.update_context_meshes()

    def read_islands(self, islands_msg):

        islands = []
        island_cnt = force_read_int(islands_msg)
        selected_cnt = force_read_int(islands_msg)

        for i in range(island_cnt):
            islands.append(read_int_array(islands_msg))

        self.p_context.set_islands(selected_cnt, islands)

    def redraw_context_area(self):

        if self.interactive:
            self.context.area.tag_redraw()

    def post_operation(self):
        pass

    def require_selection(self):
        return True

    def finish_after_operation_done(self):
        
        return not self.interactive

    def handle_operation_done(self):

        if in_debug_mode():
            print('DHPM operation time: ' + str(time.time() - self.start_time))

        self.operation_done = True

        send_finish_confirmation(self.engine_proc)

        try:
            self.engine_proc.wait(5)
        except:
            raise RuntimeError('The engine process wait timeout reached')

        self.connection_thread.join()

        engine_retcode = self.engine_proc.returncode
        self.prefs.engine_retcode = engine_retcode
        self.log_manager.log_engine_retcode(engine_retcode)
        self.check_engine_retcode(engine_retcode)

        if not self.p_context.islands_received():
            self.raiseUnexpectedOutputError()

        self.post_operation()

        if self.finish_after_operation_done():
            raise OpFinishedException()

        if self.log_manager.type_logged(DhpmLogType.ERROR):
            report_msg = 'Errors were reported'
        elif self.log_manager.type_logged(DhpmLogType.WARNING):
            report_msg = 'Warnings were reported'
        else:
            report_msg = 'Done'

        if self.log_manager.last_log(DhpmLogType.STATUS) is None:
            self.log_manager.log(DhpmLogType.STATUS, report_msg)

        hint_str = self.operation_done_hint()
        if hint_str is not None:
            self.log_manager.log(DhpmLogType.HINT, hint_str)

        if self.ov_manager is not None:
            self.ov_manager.print_dev_progress = False
            self.redraw_context_area()

    def finish(self, context):
        self.post_main()
        self.exit_common()
        return {'FINISHED', 'PASS_THROUGH'}

    def cancel(self, context):
        if self.engine_proc is not None:
            self.engine_proc.terminate()

        self.exit_common()
        return {'FINISHED'}

    def handle_engine_msg_spec(self, msg_code, msg):
        return False

    def handle_event_spec(self, event):
        return False

    def handle_out_islands_msg(self, out_islands_msg):

        out_islands = OutIslands(out_islands_msg)
        self.p_context.apply_out_islands(out_islands)

        if self.interactive:
            self.update_context_meshes()

    def handle_benchmark_msg(self, benchmark_msg):

        entry_count = force_read_int(benchmark_msg)

        for i in range(entry_count):
            dev_id = decode_string(benchmark_msg)
            dev_found = False

            for dev in self.prefs.device_array():
                if dev.id == dev_id:
                    dev_found = True
                    bench_entry = dev.bench_entry
                    bench_entry.decode(benchmark_msg)
                    break

            if not dev_found:
                self.raiseUnexpectedOutputError()

        self.redraw_context_area()

    def handle_log_msg(self, log_msg):

        log_type = force_read_int(log_msg)
        log_string = decode_string(log_msg)

        self.log_manager.log(log_type, log_string)
        # self.redraw_context_area()

    def handle_engine_msg(self, msg):

        msg_code = force_read_int(msg)

        if self.handle_engine_msg_spec(msg_code, msg):
            return

        if msg_code == DhpmMessageCode.PHASE:
            self.curr_phase = force_read_int(msg)

            # Inform the upper layer wheter it should finish
            if self.curr_phase == DhpmPhaseCode.DONE:
                self.handle_operation_done()

        elif msg_code == DhpmMessageCode.ISLANDS:

            self.read_islands(msg)

        elif msg_code == DhpmMessageCode.OUT_ISLANDS:

            self.handle_out_islands_msg(msg)

        elif msg_code == DhpmMessageCode.BENCHMARK:

            self.handle_benchmark_msg(msg)

        elif msg_code == DhpmMessageCode.LOG:

            self.handle_log_msg(msg)

        else:
            self.raiseUnexpectedOutputError()

    def enter_hang_mode(self):

        if self.hang_detected:
            return

        self.hang_detected = True
        self.hang_saved_logs = (self.log_manager.last_log(DhpmLogType.STATUS), self.log_manager.last_log(DhpmLogType.HINT))
        self.log_manager.log(DhpmLogType.STATUS, 'Engine process not responding for a longer time')
        self.log_manager.log(DhpmLogType.HINT, 'press ESC to abort or wait for the process to respond')
        
    def quit_hang_mode(self):

        if not self.hang_detected:
            return

        self.hang_detected = False
        saved_status, saved_hint = self.hang_saved_logs

        self.log_manager.log(DhpmLogType.STATUS, saved_status)
        self.log_manager.log(DhpmLogType.HINT, saved_hint)

    def handle_communication(self):

        if self.operation_done:
            return

        msg_received = 0
        while True:
            try:
                item = self.progress_queue.get_nowait()
            except queue.Empty as ex:
                break

            if isinstance(item, str):
                raise RuntimeError(item)
            elif isinstance(item, io.BytesIO):
                self.quit_hang_mode()
                self.handle_engine_msg(item)

            else:
                raise RuntimeError('Unexpected output from the connection thread')
            
            msg_received += 1

        curr_time = time.time()

        if msg_received > 0:
            self.last_msg_time = curr_time
        else:
            if self.curr_phase != DhpmPhaseCode.STOPPED and curr_time - self.last_msg_time > self.hang_timeout:
                self.enter_hang_mode()

    def handle_event(self, event):
        # Kill the DHPM process unconditionally if a hang was detected
        if self.hang_detected and event.type == 'ESC':
            raise OpAbortedException()

        if self.handle_event_spec(event):
            return

        if self.operation_done and (self.operation_num != self.prefs.operation_counter or self.operation_done_finish_condition(event)):
            raise OpFinishedException()

        if self.box_renderer is not None:
            try:
                if self.box_renderer.coords_update_needed(event):
                    self.box_renderer.update_coords()

            except Exception as ex:
                if in_debug_mode():
                    print_backtrace(ex)

                raise OpFinishedException()

        # Generic event processing code
        if event.type == 'ESC':
            if not self.cancel_sig_sent:
                self.engine_proc.send_signal(os_cancel_sig())
                self.cancel_sig_sent = True

        elif event.type == 'TIMER':
            self.handle_communication()

    def modal_ret_value(self, event):

        if self.operation_done:
            return {'PASS_THROUGH'}

        if event.type in {'MIDDLEMOUSE','WHEELDOWNMOUSE', 'WHEELUPMOUSE'}:
            return {'PASS_THROUGH'}

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        cancel = False
        finish = False

        try:
            if self.context.mode != 'EDIT_MESH':
                if self.operation_done:
                    raise OpFinishedException()

                raise RuntimeError('Edit Mode exited - operation cancelled')
            self.handle_event(event)

            if not self.operation_done and self.engine_proc.poll() is not None:
                self.handle_communication()

                if not self.operation_done:
                    self.prefs.engine_retcode = -1
                    raise RuntimeError('Engine process died unexpectedly')

        except OpFinishedException:
            finish = True

        except OpAbortedException:
            self.set_report('INFO', 'Engine process killed')
            cancel = True

        except RuntimeError as ex:
            if in_debug_mode():
                print_backtrace(ex)

            self.set_report('ERROR', str(ex))
            cancel = True

        except Exception as ex:
            if in_debug_mode():
                print_backtrace(ex)

            self.set_report('ERROR', 'Unexpected error')

            cancel = True

        if cancel:
            return self.cancel(context)

        if finish:
            return self.finish(context)

        return self.modal_ret_value(event)

    def pre_main(self):
        pass

    def post_main(self):
        pass

    def pre_operation(self):
        pass

    def scenario_in_progress(self):
        return self.engine_proc is not None

    def isolated_execution(self):
        return False

    def execute_scenario(self, scenario):

        if not check_engine():
            unregister_engine()
            redraw_ui(context)
            raise RuntimeError("DHPM engine broken")

        self.prefs.reset_stats()
        self.p_context = PackContext(self.context)

        self.pre_operation()

        send_unselected = self.send_unselected_islands()
        send_groups = self.grouping_enabled()
        send_verts_3d = self.send_verts_3d()

        iparam_serializers = self.get_iparam_serializers()

        serialized_maps, selected_cnt, unselected_cnt =\
            self.p_context.serialize_uv_maps(send_unselected, send_verts_3d, iparam_serializers)

        if self.require_selection():
            if selected_cnt == 0:
                raise NoUvFaceError('No UV face selected')
        
        else:
            if selected_cnt + unselected_cnt == 0:
                raise NoUvFaceError('No UV face visible')

        engine_args_final = [get_engine_execpath(), '-E']
        engine_args_final += ['-o', str(DhpmOpcode.EXECUTE_SCENARIO)]
        engine_args_final += ['-t', str(self.prefs.thread_count)]

        if send_unselected:
            engine_args_final.append('-s')

        if self.packing_operation():
            engine_args_final.append('-p')

        if in_debug_mode():
            if self.prefs.seed > 0:
                engine_args_final += ['-S', str(self.prefs.seed)]

            if self.prefs.wait_for_debugger:
                engine_args_final.append('-G')

            engine_args_final += ['-T', str(self.prefs.test_param)]
            print('Pakcer args: ' + ' '.join(x for x in engine_args_final))
        

        self.script_params = self.setup_script_params()
        self.script_params.add_device_settings(self.prefs.device_array())

        if self.skip_topology_parsing():
            self.script_params.add_param('__skip_topology_parsing', True)
        
        packages_dirpath = os.path.join(os.path.abspath(os.path.dirname(os.path.realpath(__file__))), SCRIPTED_PIPELINE_DIRNAME, ENGINE_PACKAGES_DIRNAME)
        scenario_dirpath = os.path.abspath(os.path.dirname(scenario['script_path']))
        self.script_params.add_sys_path(packages_dirpath)
        self.script_params.add_sys_path(scenario_dirpath)

        if self.g_scheme is not None:
            self.script_params.add_grouping_scheme(self.g_scheme, self.get_group_sparam_handler())

        out_data = self.script_params.serialize()
        out_data += serialized_maps

        if self.prefs.write_to_file:
            out_filepath = os.path.join(tempfile.gettempdir(), 'uv_islands.data')
            out_file = open(out_filepath, 'wb')
            out_file.write(out_data)
            out_file.close()


        creation_flags = os_engine_creation_flags()
        popen_args = dict()

        if creation_flags is not None:
            popen_args['creationflags'] = creation_flags

        self.engine_proc = subprocess.Popen(engine_args_final,
                                            stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE,
                                            **popen_args)

        out_stream = self.engine_proc.stdin
        out_stream.write(out_data)
        out_stream.flush()

        self.start_time = time.time()

        self.last_msg_time = self.start_time
        self.hang_detected = False
        self.hang_timeout = 10.0

        # Start progress monitor thread
        self.progress_queue = queue.Queue()
        self.connection_thread = threading.Thread(target=connection_thread_func,
                                                    args=(self.engine_proc.stdout, self.progress_queue))
        self.connection_thread.daemon = True
        self.connection_thread.start()
        self.progress_array = [0]
        self.progress_msg = ''
        self.progress_sec_left = -1
        self.progress_iter_done = -1
        self.progress_last_update_time = 0.0

        if self.interactive:
            ov_dev_array = self.prefs.dev_array if self.packing_operation() else None
            self.ov_manager = EngineOverlayManager(self, ov_dev_array)
            self.box_renderer = self.get_box_renderer()

    def execute(self, context):

        # MUSTOD: move it to __init__
        cancel = False

        self.mode = None
        self.operation_done = False
        self.engine_proc = None
        self.curr_phase = None

        self.context = context
        self.script_params = None

        self.prefs = get_prefs()
        self.scene_props = context.scene.dhpm_props

        self.p_context = None
        self.g_scheme = None

        self.ov_manager = None
        self.box_renderer = None

        self.show_region_hud_saved = None

        self.operation_num = self.prefs.operation_counter + 1
        self.prefs.operation_counter += 1


        if self.interactive and self.context.area.spaces.active.show_region_hud:
            self.show_region_hud_saved = self.context.area.spaces.active.show_region_hud
            self.context.area.spaces.active.show_region_hud = False

        try:
            if hasattr(self, 'mode_id') and self.mode_id != '':
                self.mode = self.prefs.get_mode(self.mode_id, self.context)
                self.mode.init_op(self)

            def post_log_op(log_type, log_str):
                if in_debug_mode():
                    print_log(log_str)

                self.redraw_context_area()

            self.log_manager = LogManager(post_log_op)
            self.log_manager.log(DhpmLogType.STATUS, self.STATUS_INITIAL)
            self.log_manager.log(DhpmLogType.HINT, self.HINT_INITIAL)

            self.pre_main()

            scenario_id = self.get_scenario_id()
            if scenario_id is not None:
                scenario = self.get_scenario(scenario_id)
                self.execute_scenario(scenario)

        except NoUvFaceError as ex:
            self.set_report('WARNING', str(ex))
            # cancel = True

        except RuntimeError as ex:
            if in_debug_mode():
                print_backtrace(ex)

            self.set_report('ERROR', str(ex))
            cancel = True
            
        except Exception as ex:
            if in_debug_mode():
                print_backtrace(ex)

            self.set_report('ERROR', 'Unexpected error')
            cancel = True

        if cancel:
            return self.cancel(context)

        if self.scenario_in_progress():
            if self.interactive:
                wm = context.window_manager
                self._timer = wm.event_timer_add(self.MODAL_INTERVAL_S, window=context.window)
                wm.modal_handler_add(self)
                return {'RUNNING_MODAL'}

            class FakeTimerEvent:
                def __init__(self):
                    self.type = 'TIMER'
                    self.value = 'NOTHING'
                    self.ctrl = False

            while True:
                event = FakeTimerEvent()

                ret = self.modal(context, event)
                if ret.intersection({'FINISHED', 'CANCELLED'}):
                    return ret

                time.sleep(self.MODAL_INTERVAL_S)
        else:
            self.post_main()

        return {'FINISHED'}


    def invoke(self, context, event):

        if not self.isolated_execution():
            self.interactive = True

        return self.execute(context)

    def send_unselected_islands(self):

        return self.mode_method_std_call(lambda: False, 'send_unselected_islands')

    def grouping_enabled(self):

        return self.mode_method_std_call(lambda: False, 'grouping_enabled')

    def skip_topology_parsing(self):

        return self.mode_method_std_call(lambda: False, 'skip_topology_parsing')

    def setup_script_params(self):

        return self.mode_method_std_call(lambda: ScriptParams(), 'setup_script_params')

    def get_group_method(self):

        def raise_unexpected_grouping():
            raise RuntimeError('Unexpected grouping requested')

        return self.mode_method_std_call(raise_unexpected_grouping, 'get_group_method')

    def packing_operation(self):

        return self.mode_method_std_call(lambda: False, 'packing_operation')

    def send_verts_3d(self):

        return self.mode_method_std_call(lambda: False, 'send_verts_3d')


class DHPM_OT_ScaleIslands(bpy.types.Operator):

    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.mode == 'EDIT'

    def execute(self, context):

        try:
            self.p_context = PackContext(context)
            ratio = get_active_image_ratio(self.p_context.context)
            self.p_context.scale_selected_faces(self.get_scale_factors())

        except RuntimeError as ex:
            if in_debug_mode():
                print_backtrace(ex)

            self.report({'ERROR'}, str(ex))

        except Exception as ex:
            if in_debug_mode():
                print_backtrace(ex)

            self.report({'ERROR'}, 'Unexpected error')


        self.p_context.update_meshes()
        return {'FINISHED'}

    def get_scale_factors(self):
        return (1.0, 1.0)
