from kivy.uix.scatterlayout import ScatterLayout
from kivy.properties import AliasProperty,StringProperty,BooleanProperty,NumericProperty


class ScatterBase(ScatterLayout):
    name = StringProperty()
    _hold_triggered = BooleanProperty(False)
    selected = BooleanProperty(False)
    scale_min = NumericProperty(.2)
    do_rotation = BooleanProperty(False)
    do_scale = BooleanProperty(False)
    do_translation = BooleanProperty(False)
    parent_width = NumericProperty()
    parent_height = NumericProperty()

    def get_full_bbox_parent(self, *args):
        all_corners = []
        # Can also iterate through self.content.walk(restrict=True), but takes longer
        for child in self.content.children:
            if child == self.content:
                continue
            all_corners += [child.pos, (child.x, child.top), (child.right, child.y), (child.right, child.top)]
        all_corners_parent = [self.to_parent(*point) for point in all_corners]
        xmin = min([point[0] for point in all_corners_parent])
        ymin = min([point[1] for point in all_corners_parent])
        xmax = max([point[0] for point in all_corners_parent])
        ymax = max([point[1] for point in all_corners_parent])
        return (xmin, ymin), (xmax-xmin, ymax-ymin)
    full_bbox_parent = AliasProperty(get_full_bbox_parent, None)

    # When widget is changed, check to make sure it is still in bounds of mirror
    def check_widget(self, *args):
        (bbox_x, bbox_y), (bbox_width, bbox_height) = self.full_bbox_parent

        # 1. Size check
        if bbox_width > self.parent_width:
            widget_to_bbox_ratio = bbox_width/self.parent_width
            self.scale = self.scale/widget_to_bbox_ratio
        if bbox_height > self.parent_height:
            widget_to_bbox_ratio = bbox_height/self.parent_height
            self.scale = self.scale/widget_to_bbox_ratio

        # 2. Translation check - Make sure widget is within mirror
        bbox_right = bbox_x+bbox_width
        bbox_top = bbox_y+bbox_height
        if bbox_x < 0:
            self.x -= bbox_x
        if bbox_right > self.parent_width:
            self.x += self.parent_width - bbox_right
        if bbox_y < 0:
            self.y -= bbox_y
        if bbox_top > self.parent_height:
            self.y += self.parent_height - bbox_top








