# my Input-Output Utils

import cv2
import os
import datetime
import glob

from cam_detect_cfg import cfg


class InputStream:
    def __init__(self, input_src=None):
        if input_src is None: input_src = cfg['input_source']
        self.input_source = input_src
        if self.input_source == 0 or self.input_source == '0' or self.input_source[0:7] == 'rtsp://':
            self.source_type = 'camera'
        else:
            self.source_type = 'file'
        self.handle = cv2.VideoCapture(input_src)
        self.frame_cnt = 0
        self.frame_shape = (int(self.handle.get(3)), int(self.handle.get(4)))  # (w,h)
        self.last_frame = None
        self.start_time = datetime.datetime.now()
        Log.log('input stream opened', level='info')

    def read_frame(self):
        ret, self.last_frame = self.handle.read()
        if self.handle.isOpened() == False or ret == False:
            if self.source_type == 'camera':
                Log.log('input source from camera is closed. isOpened={}, ret={}'.format(self.handle.isOpened(), ret))
                self.last_frame = self._repaired_read()
            else:
                return None
        """
        elif self.last_frame is None:
            Log.log('!!!!!!!!!!!!!!!!!!!! None frame is read !!!!!!!!!!!!!!!!!!!!!!!!!!!!!')
            self.last_frame = self._repaired_read()
        """
        self.frame_cnt += 1
        return self.last_frame

    def _repaired_read(self):
        # there was some problem with input source, try to repair, return newly read frame if ok, or None if fault
        if self.source_type == 'file':
            return None
        # source type is 'camera':
        Log.log(' Something wrong with camera stream. Trying to repair ...')
        for recapture_attempt in range(cfg['input_recapture_max']):
            del self.handle
            self.handle = cv2.VideoCapture(self.input_source)
            for reread_attempts in range(cfg['input_reread_max']):
                if cv2.waitKey(1) & 0xFF in cfg['exit_chars']:
                    Log.log('repairing of input stream has been cancelled by user')
                    return None
                ret, self.last_frame = self.handle.read()
                if ret == True and self.last_frame is not None:
                    Log.log('Input source restored after ({};{}) attempts'.format(recapture_attempt, reread_attempts))
                    return self.last_frame
        Log.log("Input source hasn't been resotored after ({};{}) attempts".format(recapture_attempt, reread_attempts))
        return None

    def info(self):
        str = ''
        str += 'Input  stream info: source={} shape={}'.format(self.input_source, self.frame_shape)
        str += 'frames={}'.format(self.frame_cnt)
        time_seconds = (datetime.datetime.now() - self.start_time).seconds
        if time_seconds != 0.:
            fps = self.frame_cnt / time_seconds
            str += ' fps={:.2f} ({:.0f}ms/img)'.format(fps, (1. / fps) * 1000)
        return str

    def __del__(self):
        self.handle.release()


class OutputStream:

    def __init__(self, file_name, frame_shape, fps=None, mode='replace_old'):
        self.frame_shape = frame_shape
        self.fps = fps if fps is not None else cfg['out_fps']
        if mode != 'replace_old':
            # for replace_old mode we write filename_seq.ext files instead of filename.ext
            fname_without_ext, file_ext = os.path.splitext(file_name)
            files_lst = glob.glob(fname_without_ext + '_*')
            numb_lst = [s[len(fname_without_ext) + 1:len(fname_without_ext) + 5] for s in files_lst]
            if len(numb_lst) == 0:
                max_numb = 0
            else:
                max_numb = max([int(s) for s in numb_lst])
            file_name = fname_without_ext + '_{:04d}'.format(max_numb + 1) + file_ext
        self.out_file_name = file_name
        self.handle = cv2.VideoWriter(self.out_file_name, cfg['out_four_cc'], self.fps, self.frame_shape)
        self.frame_cnt = 0
        self.start_time = datetime.datetime.now()
        Log.log('output stream opened: fname={} fps={} shape={}'.format(self.out_file_name, self.fps, self.frame_shape),
                level='info')

    def write_frame(self, frame):
        self.handle.write(frame)
        self.frame_cnt += 1

    def info(self):
        str = ''
        str += 'Output stream info: fname={} shape={}'.format(self.out_file_name, self.frame_shape)
        str += 'frames={}'.format(self.frame_cnt)
        time_seconds = (datetime.datetime.now() - self.start_time).seconds
        if time_seconds != 0.:
            fps = self.frame_cnt / time_seconds
            str += ' fps={:.2f} ({:.0f}ms/img)'.format(fps, (1. / fps) * 1000)
        return str

    def __del__(self):
        self.handle.release()


class UserStream:

    def wait_key(self):
        ch = cv2.waitKey(1) & 0xFF
        return False if ch in cfg['exit_chars'] else True

    def show(self, winname, frame):
        if cfg['show_output_frames'] is True: cv2.imshow(winname, frame)

    def get_key(self):
        ch = cv2.waitKey(1) & 0xFF
        return ch


# logging in-out operations
class Log:
    file_handle = None

    @staticmethod
    def log(msg, level='warning'):
        if Log.file_handle is None:
            Log.file_handle = open(cfg['log_file_name'], 'a')
        msg_str = '{:8s}: {} {}\n'.format(level, str(datetime.datetime.now())[:22], msg)
        print(msg_str)
        Log.file_handle.write(msg_str)
        Log.file_handle.flush()
