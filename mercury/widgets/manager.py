
mercury_widgets = {}
widgets_mapping = {}

def add_widget(model_id, widget):
    mercury_widgets[model_id] = widget

def get_widget(model_id):
    return mercury_widgets.get(model_id, None)

# def get_update(model_id, field):
#     w = get_widget(model_id)
#     if w is None:
#         return None    
#     return getattr(w, field)

def set_update(model_id, field, new_value):
    w = get_widget(model_id)
    if w is not None:
        setattr(w, field, new_value)