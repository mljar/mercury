import logging
import inspect

log = logging.getLogger(__name__)


mercury_widgets = {}
# widgets_mapping = {}
widget_index_to_model_id = {}
widgets_counter = 0
cell_index_to_widgets_index = {}


class WidgetException(Exception):
    pass

class WidgetsManager:

    widgets = {}        # model_id -> widget
    code2model = {}     # code generated uid  -> model_id
    cell_index = 0      # current cell index

    

    @staticmethod
    def set_cell_index(new_index):
        WidgetsManager.cell_index = new_index

    @staticmethod
    def get_code_uid():
        uid = f"{WidgetsManager.cell_index}"
        for frame in inspect.stack()[:7]:
            info = inspect.getframeinfo(frame[0])
            uid += f".{info.lineno}"
        return uid

    @staticmethod
    def widget_exists(code_uid):
        return code_uid in WidgetsManager.code2model

    @staticmethod
    def get_widget(code_uid):
        model_id = WidgetsManager.code2model.get(code_uid)
        if model_id is None:
            return None 
        return WidgetsManager.widgets.get(model_id)

    @staticmethod
    def add_widget(model_id, code_uid, widget):
        WidgetsManager.widgets[model_id] = widget
        WidgetsManager.code2model[code_uid] = model_id


    @staticmethod
    def update(model_id, field, new_value):
        # returns
        # True if there was update
        # False if no update
        w = WidgetsManager.widgets.get(model_id)
        if w is not None:
            if getattr(w, field) != new_value:
                setattr(w, field, new_value)
                return True

        return False




def set_widgets_counter(new_value):
    global widgets_counter
    widgets_counter = new_value


def widget_index_exists():
    global widgets_counter
    global widget_index_to_model_id
    return widgets_counter in widget_index_to_model_id


def get_widget_index():
    global widgets_counter
    return widgets_counter


def add_widget(model_id, widget):
    global mercury_widgets
    global widgets_counter
    mercury_widgets[model_id] = widget
    widget_index_to_model_id[widgets_counter] = model_id
    widgets_counter += 1


def get_widget(model_id):
    global mercury_widgets
    return mercury_widgets.get(model_id, None)


def get_widget_by_index():
    global widgets_counter
    global mercury_widgets
    global widget_index_to_model_id
    model_id = widget_index_to_model_id[widgets_counter]
    w = mercury_widgets.get(model_id, None)
    if w is not None:
        widgets_counter += 1
    return w


# def get_update(model_id, field):
#     w = get_widget(model_id)
#     if w is None:
#         return None
#     return getattr(w, field)


def set_update(model_id, field, new_value):
    # returns
    # True if there was update
    # False if no update
    w = get_widget(model_id)
    if w is not None:
        if getattr(w, field) != new_value:
            setattr(w, field, new_value)
            return True

    return False
