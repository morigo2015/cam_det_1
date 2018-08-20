# cam_detect
# ver 1
#
# get videostream from cam; if person appeared - send telegram message; logging all persons appeared.

import cv2
import sys
import subprocess

from cam_detect_cfg import cfg
from cam_io import InputStream, OutputStream, UserStream
from cam_dnn import PersDetector, FaceDetector, FaceRecognizer
from cam_clips import ClipManager
from util_time_measure import TimeMeasure
from cam_boxes import BGR_RED  # BGR_WHITE, BGR_GREEN,


def main():
    print('Python interpreter:{}     OpenCV version:{}'.format(sys.executable, cv2.__version__))

    pers_detector = PersDetector()
    if cfg['face_det_needed'] is True:
        face_detector = FaceDetector()
        face_recognizer = FaceRecognizer()

    # init io_util
    inp_stream = InputStream()
    user_stream = UserStream()
    if cfg['save_output_frames'] is True:
        outp_stream = OutputStream(cfg['out_file_name'], inp_stream.frame_shape, cfg['out_file_fps'],
                                   mode='replace_old')
    if cfg['save_boxed_frames'] is True:
        boxed_stream = OutputStream(cfg['boxed_file_name'], inp_stream.frame_shape, cfg['boxed_file_fps'],
                                    mode='save_old')
    if cfg['save_faced_frames'] is True:
        faced_stream = OutputStream(cfg['faced_file_name'], inp_stream.frame_shape, cfg['faced_file_fps'],
                                    mode='save_old')

    clip_mgr = ClipManager()
    time_meter = TimeMeasure(measure_needed=cfg['time_measure_needed'])

    while user_stream.wait_key() is True:
        inp_frame = inp_stream.read_frame()

        if inp_frame is None:
            event_type, event_img_fname, event_clip_fname, event_msg = clip_mgr.process_eof()
            if cfg['event_send_message'] and event_type != 'nothing':
                send_message(event_type, event_img_fname, event_clip_fname, event_msg)
            break

        outp_frame = inp_frame.copy()

        # object detection
        time_meter.set('pers detector')
        pers_boxes = pers_detector.detect(inp_frame)  # list of boxes with persons
        for pers_box in pers_boxes:
            pers_box.draw(outp_frame, color=cfg['obj_box_color'])

        if cfg['face_det_needed'] is True:

            time_meter.set('face detect & recognize')

            # face detection
            facedet_boxes = face_detector.detect(inp_frame)

            # face recognition
            boxes = [fd_box.box.sides() for fd_box in facedet_boxes]
            face_boxes = face_recognizer.recognize(inp_frame, boxes)

            # filtering some of false-positive faces
            if cfg['filter_needed']:
                # remove boxes which are not fitting into limits for w,h
                pers_boxes = [fb for fb in pers_boxes if fb.w_h_is_in_pers_range()]
                # remove boxes which are not fitting into limits for w,h
                face_boxes = [fb for fb in face_boxes if fb.w_h_is_in_face_range()]
                # remove faces which are not inside of at least one pers_box
                face_boxes = [fb for fb in face_boxes if fb.is_inside_obj_boxes(pers_boxes)]

                for face_box in face_boxes:
                    face_box.draw(outp_frame, color=BGR_RED)

        else:  # no face detection/recognition
            face_boxes = []

        # event management
        time_meter.set(' processing ')
        event_type, event_img_fname, event_clip_fname, event_msg = \
            clip_mgr.process_next_frame(inp_frame, outp_frame, pers_boxes, face_boxes)

        if cfg['event_send_message'] and event_type != 'nothing':
            send_message(event_type, event_img_fname, event_clip_fname, event_msg)

        # write outp_frame into related streams, based on cfg
        if len(pers_boxes) > 0 and cfg['save_boxed_frames'] is True:
            boxed_stream.write_frame(outp_frame)
        if len(face_boxes) > 0 and cfg['save_faced_frames'] is True:
            faced_stream.write_frame(outp_frame)
        if cfg['show_output_frames'] is True:
            user_stream.show('output frame', outp_frame)
        if cfg['save_output_frames'] is True:
            outp_stream.write_frame(outp_frame)

    # finish:
    print('\n\n', time_meter.results())
    print(inp_stream.info())
    if cfg['save_output_frames'] is True:
        print(outp_stream.info())
        del outp_stream
    del inp_stream


# end of main


def send_message(event_type, img_fname, clip_fname, msg):
    if event_type == 'appeared':
        cmd_string = f'telegram-send --image \"{img_fname}\" --caption \"{msg}\"'
    elif event_type == 'disappeared':
        cmd_string = f'telegram-send --file  \"{clip_fname}\" --caption \"{msg}\"'
    elif event_type == 'appeared-disappeared':
        cmd_string = f'telegram-send --image  \"{img_fname}\" --caption \"{msg}\" --file  \"{clip_fname}\" '
    else:
        print(f'unknown event: {event_type}')
        return

    # os.system(cmd_string)
    subprocess.Popen(cmd_string, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    # add error checking later (async), remove shell=True (overheads)
    print(cmd_string)


if __name__ == '__main__':
    main()
