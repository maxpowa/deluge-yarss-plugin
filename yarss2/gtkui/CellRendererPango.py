#
# CellRendererPango.py
#
# Copyright (C) 2012 Bro
#
# Deluge is free software.
#
# You may redistribute it and/or modify it under the terms of the
# GNU General Public License, as published by the Free Software
# Foundation; either version 3 of the License, or (at your option)
# any later version.
#
# deluge is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.
# See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with deluge.    If not, write to:
#       The Free Software Foundation, Inc.,
#       51 Franklin Street, Fifth Floor
#       Boston, MA  02110-1301, USA.
#
#    In addition, as a special exception, the copyright holders give
#    permission to link the code of portions of this program with the OpenSSL
#    library.
#    You must obey the GNU General Public License in all respects for all of
#    the code used other than OpenSSL. If you modify file(s) with this
#    exception, you may extend this exception to your version of the file(s),
#    but you are not obligated to do so. If you do not wish to do so, delete
#    this exception statement from your version. If you delete this exception
#    statement from all source files in the program, then also delete it here.
#

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

class CellRendererPango(gtk.CellRendererText):

    __gproperties__ = {
        "custom": (CustomAttribute, "custom",
                   "custom", gobject.PARAM_READWRITE),
        }

    property_names = __gproperties__.keys()

    def __init__(self):
        gtk.CellRendererText.__init__(self)
        self.include_color_string = "#5acf36" # Green
        self.exclude_color_string = "#f31010" # Red
        self.include_color = gtk.gdk.color_parse(self.include_color_string)
        self.exclude_color = gtk.gdk.color_parse(self.exclude_color_string)

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
        customAttr = self.get_property("custom")

        def set_attr(layout):
            attr = pango.AttrList()
            size = pango.AttrSize(int(11.5 * pango.SCALE), 0, -1)
            attr.insert(size)
            if customAttr and customAttr.attributes_dict:
                attributes_dict = customAttr.attributes_dict

                if attributes_dict.has_key("regex_include_match"):
                    start, end = attributes_dict["regex_include_match"]
                    pango_color = pango.AttrBackground(self.include_color.red, self.include_color.green,
                                                       self.include_color.blue, start, end)
                    attr.insert(pango_color)
                if attributes_dict.has_key("regex_exclude_match"):
                    start, end = attributes_dict["regex_exclude_match"]
                    pango_color = pango.AttrForeground(self.exclude_color.red, self.exclude_color.green,
                                                       self.exclude_color.blue, start, end)
                    attr.insert(pango_color)
            layout.set_attributes(attr)

        text = self.get_text()
        layout.set_text(text)
        set_attr(layout)

        # Vertically align the text
        #cell_area.y += 2
        #cell_area.x += 1

        cairo_context.move_to(cell_area.x, cell_area.y)
        cairo_context.show_layout(layout)

    def do_get_size(self, widget, cell_area=None):
        return gtk.CellRendererText.do_get_size(self, widget, cell_area)

gobject.type_register(CellRendererPango)
