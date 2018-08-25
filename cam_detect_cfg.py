# cam_detec_config

import cv2

_folders = {
    'video'        : 'production/videos/' ,
    'models'       : 'production/models/' ,
    'face_dataset' : 'production/face_dataset/' ,
    'event_images' : 'production/event_images/'
}

cfg = {
     'show_output_frames'   : True ,  # show output frames on screen (imshow(...)

    'input_source'         : 0 ,
    #'input_source'         : 'production/videos/room-faces.avi' ,
    #'input_source'         : 'rtsp://admin:F1123581321f@192.168.1.64:554/Streaming/Channels/101' ,  # hik cam
    #'input_source'          : 'rtsp://admin:F112358f@192.168.1.165:554/Streaming/Channels/101' ,  # door bell

    'input_recapture_max'   : 1000 ,     # max attempts to reopen cv2.VideoCapture
    'input_reread_max'      : 1000 ,   # max attempts to reread frame after reopen VideoCapture

    #'save_output_frames'    : True ,  # save output (all!) frames to file
    'save_output_frames'    : False ,  # save output (all!) frames to file
    'out_file_name'         : _folders['video']+'output.avi' ,
    'out_four_cc'           : cv2.VideoWriter_fourcc( *'XVID') ,
    'out_file_fps'          : 20 ,

    'save_boxed_frames'     : False , # to save in videofile boxed frames
    'boxed_file_name'       : _folders['video']+'boxed.avi' ,
    'boxed_file_fps'        : 20 ,

    'save_faced_frames'     : True,  # to save in videofile boxed frames
    'faced_file_name'       : _folders['video']+'faced.avi' ,
    'faced_file_fps'        : 5 ,

    'obj_box_color'         : (0, 255, 0) , # greem
    'face_box_color'        : (0, 0, 255) , # red

    'pers_det_prototxt'     : _folders['models']+'MobileNetSSD_deploy.prototxt.txt' ,
    'pers_det_model'        : _folders['models']+'MobileNetSSD_deploy.caffemodel' ,
    'pers_det_confidence'   : 0.4 , # confidence threshold
    'pers_box_width_range'   : (30, 1200),  # (min,max) range for persbox width
    'pers_box_height_range'  : (30, 700),  # (min,max) range for persbox height
    'pers_box_wh_ratio_range': (0.25, 1./0.25),  # (min,max) range for persbox width/height

    'facedataset_folder'    : _folders['face_dataset'],
    'encodings_file'        : _folders['face_dataset']+'face_encodings.pkl',

    #'face_needed'           : True , # include face processing: detection,encoding,classification
    'face_needed'           : False ,
    'face_det_prototxt'     : _folders['models']+'face_deploy.prototxt.txt' ,
    'face_det_model'        : _folders['models']+'face_res10_300x300_ssd_iter_140000.caffemodel' ,
    'face_det_confidence'   : 0.2 ,  # confidence threshold
    'face_box_width_range'  : (30,600) , # (min,max) range for facebox width
    'face_box_height_range' : (30,600)  , # (min,max) range for facebox height
    'face_box_wh_ratio_range':  (0.75,1./0.75) , # (min,max) range for facebox width/height

    'face_rec_use_threshold': True, # if distance to nearest neighbor < Threshold: label="Unknown"
    'face_rec_threshold'    : -1 , # -1: calculate threshold on encodings; else: the value is (manually set) threshold

    'filter_needed'         : False ,# check pers_box,obj_box for wh_range; check for face_box that outer pers_box exists
    'time_measure_needed'   : True ,# time measure in main loop of cam_detect

    'clips_fname_prefix'    : _folders['video']+'clip_' ,
    'clips_fname_suffix'    : '.avi' ,
    'clips_labelled_prefix' : _folders['video'] ,
    'clips_include_boxes'   : True,  # include pers box (green) in clip
    'clips_prev_frames'             : 10 , # how many previous frames include in the begin of clip
    'clips_noperson_frames_to_stop' : 25 , # how many frames without person are allowed to not stop clip
    'clips_frames_to_appear'        : 30 , # how many frames in clip to allow announce 'appear' event (once per clip)
    'clips_fps'                     : 10 ,

    'event_send_message'        : True , # send telegram msg
    'event_image_folder'        : _folders['event_images'],
    'event_image_ext'           : '.jpg' ,

    'face_labels_list'          : ['Yulka', 'Yehor', 'Olka', 'Igor', 'Ded'] ,

# utils:
    'util_clip_folder'          : _folders['video'] ,
    'util_clip_input'           : 'clip*',

# clips-->labelled images:
    'util_raw_clips_folder'     : 'preparation/raw_clips/' ,       # здесь лежать клипы (по папкам)
    'util_img_folder'           : 'preparation/labelled_images/' , # куда складывать images (по папкам)
    'lbl_images_boxed_folder'   : 'preparation/labelled_images/_boxed_images/' ,  # for util_clip_img
    'lbl_images_boxed_needed'   : True ,

# labelled images --> encodings
    'encoding_boxed_folder'     : _folders['face_dataset']+'_boxed_images/_after_encoding/' ,
    'encoding_boxed_needed'     : True , # create and save boxed imaged when prepare embeddings

# util - test recginizer
    'test_images_folder'           : 'preparation/test_images_folder/' ,

#util - split to train,test
    'boxed_folder'              : 'preparation/labelled_images/_boxed_images/' ,
    'labelled_folder'           : 'preparation/labelled_images/' ,
    'train_folder'              : 'preparation/labelled_images/_train/' ,

    'log_file_name'             : 'log.txt',
    'exit_chars'                : [ord('q'), ord('Q'), 27]  # ord(ESC)=27
}