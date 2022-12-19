import logging

log = logging.getLogger(__name__)


mercury_widgets = {}
# widgets_mapping = {}
widget_index_to_model_id = {}
widgets_counter = 0
cell_index_to_widgets_index = {}


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
