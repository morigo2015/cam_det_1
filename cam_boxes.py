# Boxes

import cv2

from cam_detect_cfg import cfg

BGR_BLACK = (0, 0, 0)
BGR_RED = (0, 0, 255)
BGR_GREEN = (0, 255, 0)
BGR_BLUE = (255, 0, 0)
BGR_WHITE = (255, 255, 255)


class Box:

    # colour = BGR_GREEN  # default colour for box (green)

    def __init__(self, startX=None, startY=None, endX=None, endY=None, coordinate_str=None
                 , sides_tuple=None):
        """
        create new box based on corners coordinates or corner-order string
        :param coordinate_str: corner-order string
        """
        if coordinate_str is not None:  # init from string, usually - part of file name
            self.startX, self.startY, self.endX, self.endY = Box.str_2_coord(coordinate_str)
        elif startX is not None and startY is not None and endX is not None and endY is not None:
            self.startX = startX
            self.startY = startY
            self.endX = endX
            self.endY = endY
        elif sides_tuple is not None:
            self.startX, self.startY, self.endX, self.endY = Box.sides_2_corners(sides_tuple=sides_tuple)
        else:
            print('!!!!! error while initializing Box !!!!!! ')

    def draw(self, frame, color=None, label=None):
        if color is None:
            color = BGR_GREEN
        cv2.rectangle(frame, (self.startX, self.startY), (self.endX, self.endY), color, 2)
        if label is not None:
            y = self.startY - 15 if self.startY - 15 > 15 else self.startY + 15
            cv2.putText(frame, label, (self.startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.75, color, 2)

    def sides(self):
        # return top,right,bottom,left
        return self.startY, self.endX, self.endY, self.startX

    def corners(self):
        return self.startX, self.startY, self.endX, self.endY

    @staticmethod
    def width(corners_tuple=None, sides_tuple=None):
        if sides_tuple is not None:
            top, right, bottom, left = sides_tuple
            return right - left
        return

    @staticmethod
    def height(corners_tuple=None, sides_tuple=None):
        if sides_tuple is not None:
            top, right, bottom, left = sides_tuple
            return bottom - top
        return

    def __eq__(self, other):
        if isinstance(other, Box):
            return self.startX == other.startX and self.startY == other.startY \
                   and self.endX == other.endX and self.endY == other.endY
        return NotImplemented

    def box_2_str(self):
        """
        coordinates of existing box --> string for filename (in corners-order)
        return 'corners'-order(sXYeXY), not 'sides'-order(trbl) !!
        """
        return '{:04d}{:04d}{:04d}{:04d}'.format(self.startX, self.startY, self.endX, self.endY)

    @staticmethod
    def str_2_coord(str):
        """
        string for filename -->  box coordinates
        """
        startX = int(str[0:4])
        startY = int(str[4:8])
        endX = int(str[8:12])
        endY = int(str[12:16])
        return startX, startY, endX, endY

    @staticmethod
    def coord_2_str(startX, startY, endX, endY):
        """
        box coordinates  -->  string for filename
        """
        str = '{:04d}{:04d}{:04d}{:04d}'.format(startX, startY, endX, endY)
        return str

    # conversion:    sides-order (top,right,bottom,left)   <--->   corners-order  (startX,startY,endX,endY)

    @staticmethod
    def corners_2_sides(startX=None, startY=None, endX=None, endY=None
                        , corners_tuple=None):
        if corners_tuple is not None:
            (startX, startY, endX, endY) = corners_tuple
        return startY, endX, endY, startX

    @staticmethod
    def sides_2_corners(top=None, right=None, bottom=None, left=None
                        , sides_tuple=None):
        if sides_tuple is not None:
            top, right, bottom, left = sides_tuple
        return left, top, right, bottom

    # string conversion: sides-order  <---> corners-order
    # each value - 4 digits

    @staticmethod
    def corners_2_sides_str(str):
        (startX, startY, endX, endY) = Box.str_2_coord(str)
        (left, top, right, bottom) = Box.corners_2_sides(startX, startY, endX, endY)
        return Box.coord_2_str(left, top, right, bottom)

    @staticmethod
    def sides_2_corners_str(str):
        (left, top, right, bottom) = Box.str_2_coord(str)
        (startX, startY, endX, endY) = Box.sides_2_corners(left, top, right, bottom)
        return Box.coord_2_str(startX, startY, endX, endY)

    @staticmethod
    def test():
        print('testing Box class:')
        box1 = Box(10, 15, 200, 300)
        str = Box.coord_2_str(10, 15, 200, 300)
        box2 = Box(coordinate_str=str)
        if box1 != box2:
            print('error. box1={}  box2={}'.format(box1, box2))

        t, r, b, l = Box.str_2_coord(Box.corners_2_sides_str(box1.box_2_str()))
        sx, sy, ex, ey = Box.sides_2_corners(t, r, b, l)
        box3 = Box(sx, sy, ex, ey)
        if box3 != box1:
            print('error. box1={}  box3={}'.format(box1, box3))


# --------------------------------------------------------------------------------------------------------

class ObjBox:

    def __init__(self, startX=None, startY=None, endX=None, endY=None, confidence=None, idx=None, label=None
                 , sides_tuple=None):
        if sides_tuple is not None:
            self.box = Box(sides_tuple=sides_tuple)
        else:
            self.box = Box(startX, startY, endX, endY)

        self.confidence = confidence if confidence is not None else -1.0
        self.idx = idx if idx is not None else -1
        self.label = label if label is not None else "unknown"

        self.face_box = None
        self.face_id = None

    def draw(self, frame, color=None):
        if color is None:
            color = BGR_GREEN
        self.box.draw(frame, color)
        label_txt = self.label if self.label is not None else ''
        confid_txt = f'd={self.confidence:.3f}' if self.confidence is not None else ''
        y = self.box.startY - 15 if self.box.startY - 15 > 15 else self.box.startY + 15
        cv2.putText(frame, f'{label_txt}  {confid_txt}', (self.box.startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

    def is_inside_box(self, box):
        top_box, right_box, bottom_box, left_box = box.sides()
        top, right, bottom, left = self.box.sides()
        if top >= top_box and right <= right_box and bottom <= bottom_box and left >= left_box:
            return True
        return False

    def is_inside_obj_boxes(self, obj_boxes_lst):
        for obj_box in obj_boxes_lst:
            if self.is_inside_box(obj_box.box):
                return True
        return False

    def w_h_is_in_face_range(self):
        w = self.box.endX - self.box.startX
        h = self.box.endY - self.box.startY

        if not (cfg['face_box_width_range'][0] <= w <= cfg['face_box_width_range'][1]):
            return False
        if not (cfg['face_box_height_range'][0] <= h <= cfg['face_box_height_range'][1]):
            return False
        if not (cfg['face_box_wh_ratio_range'][0] <= float(w) / float(h) <= cfg['face_box_wh_ratio_range'][1]):
            return False

        return True

    def w_h_is_in_pers_range(self):
        w = self.box.endX - self.box.startX
        h = self.box.endY - self.box.startY
        if not (cfg['pers_box_width_range'][0] <= w <= cfg['pers_box_width_range'][1]):
            return False
        if not (cfg['pers_box_height_range'][0] <= h <= cfg['pers_box_height_range'][1]):
            return False
        if not (cfg['pers_box_wh_ratio_range'][0] <= float(w) / float(h) <= cfg['pers_box_wh_ratio_range'][1]):
            return False

        return True


# -------------------------------------------------------------------------------------------------------------

if __name__ == '__main__':
    Box.test()
