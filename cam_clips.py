# cut input stream of frames into clips
# clip - short video file where person is presenting plus several frames just before and after
# return events:
# 'appeared' : person is presenting some (fixed) amount of frames from the beginning.
#              Best image is storing to file; filename is passing to event
# 'disappeared':  person is absent some (fixed) amount of frames
#                 file with clip is closing; filename is passing to event
# 'appeared-disappeared:
# when several persons simultaneously:
# current version - treat them as one (person present, never mind how many)
# next versions - to support several persons flow (join them based on box interception)

import subprocess
from collections import deque
import cv2
import datetime
import os

from cam_io import InputStream, OutputStream, UserStream
from cam_detect_cfg import cfg


class ClipManager:

    def __init__(self):
        self.clip = None  # None - noone clip is not started now
        self.best_faces_lst = None
        self.best_pers_info = None
        self.noperson_frame_cnt = 0  # how many seq frames person is absent (inside clip)
        self.appeared = False  # has 'appeared' event been already anounced for current clip

    def process_next_frame(self, inp_frame, outp_frame, pers_boxes, face_boxes):

        frame = outp_frame if cfg['clips_include_boxes'] else inp_frame

        _PrevBuffer.process_next_frame(frame)

        if self.clip is None:  # we are not clipping now

            if not len(pers_boxes):  # no persons
                return 'nothing', '', '', ''

            # persons are found in the frame, out of clip
            self.clip = _Clip(frame)  # start new clip
            self.best_faces_lst = _BestFacesInfo()
            self.best_pers_info = _BestPersInfo()
            self.noperson_frame_cnt = 0  # how many seq frames person is absent (inside clip)
            self.appeared = False  # has 'appeared' event been already anounced for current clip

        # self.clip != None  : we are in clip now
        self.clip.append_frame(frame)

        if len(pers_boxes):  # there are persons

            self.noperson_frame_cnt = 0
            self.best_faces_lst.update(frame, face_boxes)
            self.best_pers_info.update(frame,pers_boxes)

            if self.clip.frame_cnt >= cfg['clips_frames_to_appear'] and not self.appeared:
                # 'appeared' occured
                self.appeared = True  # no more 'appeared' event in the clip
                best_img_fname = self.best_img_fname()
                msg = self.best_faces_lst.faces_str(include_distances=True)
                return 'appeared', best_img_fname, '', msg

        else:  # no persons

            self.noperson_frame_cnt += 1  # one more sequential frame without person inside the clip

            if self.noperson_frame_cnt == cfg['clips_noperson_frames_to_stop']:  # person is absent too long

                if not self.appeared:
                    # appeared-disappeared occured
                    best_img_fname = self.best_img_fname()
                    msg = self.best_faces_lst.faces_str(include_distances=True, sep=' ')
                    best_clip_fname = self._rename_clip()
                    # closing clip. todo rearrange into common-used funcions/methods
                    self.clip.close()
                    self.clip = None
                    # del self.best_faces_lst
                    self.best_faces_lst = None
                    self.best_pers_info = None
                    return 'appeared-disappeared', best_img_fname, best_clip_fname, msg

                # 'disappeared' occured

                if self.best_faces_lst.best_lable is not None:
                    new_clip_fname = self._rename_clip()
                else:
                    print('no faces in this clip')
                    new_clip_fname = self.clip.file_name

                # closing clip. todo rearrange into common-used funcions/methods
                self.clip.close()
                self.clip = None
                # del self.best_faces_lst
                self.best_faces_lst = None
                self.best_pers_info = None
                return 'disappeared', '', new_clip_fname, 'Person has left.'

        return 'nothing', '', '', ''

    def process_eof(self):
        """
        is called once when end of input stream received;
        there is no frame, *_boxes, etc.; just complete clip if it is opened.
        """
        if self.clip is None:  # clip hasn't started yet
            return 'nothing', '', '', ''

        if self.best_faces_lst.best_lable is None:  # there were no faces in clip, nothing to worry about
            return 'nothing', '', '', ''

        # here: clip opened, faces occured
        if not self.appeared:
            # there was faces in opened clip and 'appeared'-event has not been triggered yet
            self.appeared = True
            best_img_fname = self.best_img_fname()
            msg = self.best_faces_lst.faces_str(include_distances=True, sep=' ')
            return 'appeared-disappeared', best_img_fname, self._rename_clip(), msg

        else:  # self.appeared == True
            new_clip_name = self._rename_clip()
            self.clip.close()
            self.clip = None
            # del self.best_faces_lst
            return 'disappeared', '', new_clip_name, 'Persons found'

    def best_img_fname(self):
        """
        :return: file name for file which is the best image for this clip (best faces if occured else best pers)
        """
        if self.best_faces_lst.best_lable is not None:
            # faces occured in clip, so best img is best face img
            return self.best_faces_lst.img_fname()

        return self.best_pers_info.best_pers_image_fname()

    def _rename_clip(self):
        old_clip_fname = self.clip.file_name
        faces_str = self.best_faces_lst.faces_str(include_distances=False)
        fname = self.clip.file_name.split(sep="/")[-1]
        new_clip_fname = f'{cfg["clips_labelled_prefix"]}{faces_str}_{fname}'
        cmd_str = f'mv \"{old_clip_fname}\" \"{new_clip_fname}\"'
        subprocess.Popen(cmd_str, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        # add error checking later (async), remove shell=True (overheads)
        print(f'execute: {cmd_str}')
        return new_clip_fname

# ---------------------------------------------------------------------------------------------------------------


class _PrevBuffer:
    """
    manages buffer of several previous frames;
    they will be written at the beginning of clip before first frame with person
    """

    buffered_frames_cnt = 0
    frame_buffer = deque([])

    @staticmethod
    def process_next_frame(frame):
        _PrevBuffer.frame_buffer.append(frame)
        if _PrevBuffer.buffered_frames_cnt < cfg['clips_prev_frames']:  # we are still filling buffer at start
            _PrevBuffer.buffered_frames_cnt += 1
        else:  # buffer is initialized already
            _PrevBuffer.frame_buffer.popleft()

    @staticmethod
    def get_prev_frames():
        # return list of previous frames
        return list(_PrevBuffer.frame_buffer)


class _BestPersInfo:
    """
    manage info about best person (objects) in clip
    Best means max obj(pers) confidence.
    """
    def __init__(self):
        self.best_image = None
        self.best_conf = -1

    def update(self,frame,pers_boxes):
        for pb in pers_boxes:
            if self.best_conf is None or pb.confidence > self.best_conf:
                self.best_conf = pb.confidence
                self.best_image = frame.copy()
                continue

    def best_pers_image_fname(self):
        os.makedirs(cfg['event_image_folder'],exist_ok=True)
        fname = f"{cfg['event_image_folder']}/{datetime.datetime.now()}{cfg['event_image_ext']}"
        cv2.imwrite(fname, self.best_image)
        return fname


class _BestFacesInfo:
    """
    manages info about occured faces:
    """

    def __init__(self):
        self.labels_best_dist = {}  # { 'label' : label, 'best_dist' : dist } for faces occured in the clip
        self.best_image = None  # outp frame copy for the best face
        self.best_distance = None  # distance for the best face
        self.best_lable = None  # label of the best face
        self.label_cnt = {}

    def update(self, frame, face_boxes):
        """
        update best face info, based on current frame
        """

        for fb in face_boxes:

            try:
                self.label_cnt[fb.label] += 1
            except KeyError:
                self.label_cnt[fb.label] = 1

            if self.best_lable is None:
                # no one face occured yet
                self._be_the_best(fb, frame)
                continue

            if fb.label not in self.labels_best_dist:  # new label, never occured before
                self.labels_best_dist[fb.label] = fb.confidence
                continue

            if fb.confidence < self.labels_best_dist[fb.label]:
                # new best face for fb.label
                self.labels_best_dist[fb.label] = fb.confidence
                if fb.confidence < self.best_distance:
                    # new the best face
                    self._be_the_best(fb, frame)

    def _be_the_best(self, face_box, frame):
        self.labels_best_dist[face_box.label] = face_box.confidence
        self.best_lable = face_box.label
        self.best_distance = face_box.confidence
        self.best_image = frame.copy()

    def img_fname(self):
        """
        return name of file with saved image of best image in the clip. Best means - best (shortest) face distance.
        """
        os.makedirs(cfg['event_image_folder'],exist_ok=True)
        fname = f"{cfg['event_image_folder']}/{datetime.datetime.now()}{cfg['event_image_ext']}"
        cv2.imwrite(fname, self.best_image)
        return fname

    def faces_str(self, include_distances=True, include_counters=True, sep=','):
        """
        :return: caption: list of occured faces
        """
        msg = ''
        for lbl in self.labels_best_dist:
            msg += f"{lbl}"
            if include_distances:
                msg += f"(d={self.labels_best_dist[lbl]:4.2f})"
            if include_counters:
                msg += f"(cnt={self.label_cnt[lbl]})"
            msg += sep
        if msg and msg[-1] == sep:
            msg.rstrip(sep)

        if not msg:
            msg = 'no_faces'
        return msg


class _Clip:

    def __init__(self, frame):
        self.file_name = '{}{}{}'.format(cfg['clips_fname_prefix'], datetime.datetime.now(), cfg['clips_fname_suffix'])
        self.frame_cnt = 0
        (h, w) = frame.shape[0:2]
        self.handle = OutputStream(self.file_name, (w, h), cfg['clips_fps'], mode='replace_old')
        # at start: write previous frames stored in buffer
        for f in _PrevBuffer.get_prev_frames():
            self.handle.write_frame(f)
            self.frame_cnt += 1
        print('created new clip: {}'.format(self.file_name))

    def append_frame(self, frame):
        self.handle.write_frame(frame)
        self.frame_cnt += 1

    def close(self):
        print('clip {} closed. Frames:{}'.format(self.file_name, self.frame_cnt))
        del self.handle


# ----------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':

    def test_prev_buff():
        inp_stream = InputStream(input_src=0)
        user_stream = UserStream()
        cnt = 0
        cfg['clips_prev_frames'] = 200
        c = None
        while True:
            ch = user_stream.get_key()
            if ch in cfg['exit_chars']:
                break
            inp_frame = inp_stream.read_frame()
            cnt += 1
            if cnt < cfg['clips_prev_frames']:
                _PrevBuffer.process_next_frame(inp_frame)
                user_stream.show('buffer', inp_frame)
            if ch == ord(' '):
                for f in _PrevBuffer.get_prev_frames():
                    user_stream.show('output frame', f)
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

    # test_prev_buff()
