# cut input stream of frames into clips
# clip - short video file where person is presenting plus several frames just before and after
# return events:
# 'appeared' : person is presenting some (fixed) amount of frames from the beginning.
#              Best image is storing to file; filename is passing to event
# 'disappeared':  person is absent some (fixed) amount of frames
#                 file with clip is closing; filename is passing to event
# when several persons simultaneously:
# current version - treat them as one (person present, never mind how many)
# next versions - to support several persons flow (join them based on box interception)

from collections import deque
import cv2

from cam_detect_cfg import cfg

class ClipManager:

    def __init__(self):
        self.clip = None # None - noone clip is not started now
        self.noperson_frame_cnt = 0  # how many seq frames person is absent (inside clip)
        self.appeared = False # has 'appeared' event been already anounced for current clip

    def process_next_frame(self,inp_frame,outp_frame,pers_boxes):

        self.last_event = 'nothing'
        self.last_event_fname = ''
        self.last_event_msg = ''

        frame = outp_frame if cfg['clips_include_boxes'] else inp_frame

        _PrevBuffer.process_next_frame(frame)

        if self.clip is None:  # we are not clipping now

            if len(pers_boxes)>0: # person in frame
                self.clip = _Clip(frame)
                self.noperson_frame_cnt = 0  # how many seq frames person is absent (inside clip)
                self.appeared = False # has 'appeared' event been already anounced for current clip

        else:  # self.clip != None   : we are in clip now

            self.clip.append_frame(frame)

            if len(pers_boxes)==0 :  # no person

                self.noperson_frame_cnt += 1 # one more sequential frame without person inside the clip

                if self.noperson_frame_cnt == cfg['clips_noperson_frames_to_stop']: # person is absent too long - stop the clip
                    self.last_event = 'disappeared'
                    self.last_event_fname = self.clip.file_name
                    self.clip.close()
                    self.clip = None

            else:  # len(pers_boxes) >0:  # person in frame

                    self.noperson_frame_cnt = 0

                    if self.clip.frame_cnt >= cfg['clips_frames_to_appear'] and self.appeared == False:
                        self.appeared = True # no more 'appeared' event in the clip
                        self.last_event_fname = self.clip.best_img_fname(frame)
                        self.last_event = 'appeared'
                        pers_box = pers_boxes[0]
                        conf = pers_box.confidence
                        self.last_event_msg = "unknown. conf={:.2f}".format( conf ) # !!!! ***** change for multi-person image !!!!!! ******

        return self.last_event,self.last_event_fname,self.last_event_msg

class _PrevBuffer:
    # buffer of several previous frames; they will be written at the beginning of clip before first frame with person
    buffered_frames_cnt = 0
    frame_buffer = deque([])

    @staticmethod
    def process_next_frame(frame):
        _PrevBuffer.frame_buffer.append(frame)
        if _PrevBuffer.buffered_frames_cnt < cfg['clips_prev_frames']: # we are still filling buffer at start
            _PrevBuffer.buffered_frames_cnt += 1
        else: # buffer is initialized already
            _PrevBuffer.frame_buffer.popleft()

    @staticmethod
    def get_prev_frames():
        # return list of previous frames
        return list(_PrevBuffer.frame_buffer)

from cam_io    import InputStream, OutputStream, UserStream
import datetime

class _Clip:

    def __init__(self,frame):
        self.file_name = '{}{}{}'.format(cfg['clips_fname_prefix'],datetime.datetime.now(),cfg['clips_fname_suffix'])
        self.frame_cnt = 0
        (h,w) = frame.shape[0:2]
        self.handle = OutputStream(self.file_name,(w,h),cfg['clips_fps'],mode='replace_old')
        # at start: write previous frames stored in buffer
        for f in _PrevBuffer.get_prev_frames():
            self.handle.write_frame(f)
            self.frame_cnt += 1
        print('created new clip: {}'.format(self.file_name))

    def close(self):
        print('clip {} closed. Frames:{}'.format(self.file_name, self.frame_cnt))
        del self.handle

    def append_frame(self,frame):
        self.handle.write_frame(frame)
        self.frame_cnt += 1

    def best_img_fname(self,frame):
        fname = '{}/{}{}'.format(cfg['event_image_folder'], datetime.datetime.now(), cfg['event_image_ext'])
        cv2.imwrite(fname, frame)
        return fname

def test_prev_buff():
    inp_stream = InputStream(input_src=0)
    user_stream = UserStream()
    cnt = 0
    cfg['clips_prev_frames'] = 200
    c = None
    while True:
        ch = user_stream.get_key()
        if ch in cfg['exit_chars']: break
        inp_frame = inp_stream.read_frame()
        cnt+=1
        if cnt < cfg['clips_prev_frames']:
            _PrevBuffer.process_next_frame(inp_frame)
            user_stream.show('buffer',inp_frame)
        if ch == ord(' '):
            for f in _PrevBuffer.get_prev_frames():
                user_stream.show('output frame',f)
                user_stream.wait_key()
        if ch == ord('i'):
            c = _Clip(inp_frame)
            continue
        if ch == ord('e'):
            c.close()
            c = None
            continue
        if c is not None:
            c.append_frame(inp_frame)
        _PrevBuffer.process_next_frame(inp_frame)
        user_stream.show('output frame', inp_frame)

if __name__ == '__main__':
    test_prev_buff()