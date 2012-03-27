
import gtk
import pango
import pangocairo
import cairo
import cgi
import gobject

class CustomAttribute(gobject.GObject, object):
    def __init__(self, attributes_dict=None):
        super(CustomAttribute, self).__init__()
        self.attributes_dict = attributes_dict

gobject.type_register(CustomAttribute)

class CellrendererPango(gtk.CellRendererText):
   
    __gproperties__ = {
        "custom": (CustomAttribute, "custom",
                   "custom", gobject.PARAM_READWRITE),
        }
    
    property_names = __gproperties__.keys()
        
    def __init__(self):
        gtk.CellRendererText.__init__(self)

    def __getattr__(self, name):
        try:
            return self.get_property(name)
        except TypeError:
            raise AttributeError

    def __setattr__(self, name, value):
        try:
            self.set_property(name, value)
        except TypeError:
            self.__dict__[name] = value

    def do_get_property(self, property):
        if property.name not in self.property_names:
            raise TypeError('No property named %s' % (property.name,))
        return self.__dict__[property.name]

    def do_set_property(self, property, value):
        if property.name not in self.property_names:
            raise TypeError('No property named %s' % (property.name,))
        self.__dict__[property.name] = value

    def get_text(self):
        value = self.get_property('text')
        return value

    def get_layout(self, widget):
         '''Gets the Pango layout used in the cell in a TreeView widget.'''
         layout = pango.Layout(widget.get_pango_context())
         layout.set_width(-1)    # Do not wrap text.
         return layout

    def do_render(self, window, widget, background_area, cell_area, expose_area, flags):
        cairo_context = pangocairo.CairoContext(window.cairo_create())
        layout = self.get_layout(widget)
        
        #include_color_string = "#2400ff"
        include_color_string = "#73a6f9"
        exclude_color_string = "#f31010"
               
        include_color = gtk.gdk.color_parse(include_color_string)
        exclude_color = gtk.gdk.color_parse(exclude_color_string)
        
        attributes_dict = {}
        attributes_dict["regex_include_match"] = (0, 17)
        attributes_dict["regex_exclude_match"] = (14, 30)
        customAttr = CustomAttribute(attributes_dict=attributes_dict)
        customAttr = self.get_property("custom")
    
        def set_attr(layout):
            if customAttr and customAttr.attributes_dict:
                attributes_dict = customAttr.attributes_dict
                attr = pango.AttrList()
                if attributes_dict.has_key("regex_include_match"):
                    start, end = attributes_dict["regex_include_match"]
                    pango_color = pango.AttrBackground(include_color.red, include_color.green, 
                                                    include_color.blue, start, end)
                    attr.insert(pango_color)
                if attributes_dict.has_key("regex_exclude_match"):
                    start, end = attributes_dict["regex_exclude_match"]
                    pango_color = pango.AttrForeground(exclude_color.red, exclude_color.green, 
                                                    exclude_color.blue, start, end)
                    attr.insert(pango_color)
                layout.set_attributes(attr)
        
        text = unicode(self.get_text())

        set_attr(layout)
        layout.set_text(text)
        cairo_context.move_to(cell_area.x, cell_area.y)
        cairo_context.show_layout(layout)

    def do_get_size(self, widget, cell_area=None):
        #return (0, 0, self.custom.get_width(), self.custom.get_height())
        return gtk.CellRendererText.do_get_size(self, widget, cell_area)

gobject.type_register(CellrendererPango)
