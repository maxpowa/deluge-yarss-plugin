/**
 * yarss2.js
 *
# Copyright (C) 2019 bendikro bro.devel+yarss2@gmail.com
 *
 * This file is part of Deluge and is licensed under GNU General Public License 3.0, or later, with
 * the additional special exception to link portions of this program with the OpenSSL library.
 * See LICENSE for more details.
 *
 */

Ext.ns('Deluge.ux.preferences');

/**
 * @class Deluge.ux.preferences.YaRSS2Page
 * @extends Ext.Panel
 */
Deluge.ux.preferences.YaRSS2Page = Ext.extend(Ext.Panel, {
    title: _('YaRSS2'),
    layout: 'fit',
    border: false,
    header: false,

    initComponent: function() {
        Deluge.ux.preferences.YaRSS2Page.superclass.initComponent.call(this);
        fieldset = this.add({
            xtype: 'fieldset',
            border: false,
            title: _('YaRSS2 Preferences'),
            autoHeight: true,
            labelWidth: 1,
            defaultType: 'panel',
        });
        fieldset.add({
            border: false,
            bodyCfg: {
                html: _(
                    '<p>The YaRSS2 plugin must be managed through the GTK UI client.</p>'
                ),
            },
        });
    },
});

Ext.ns('Deluge.ux');
Ext.ns('Deluge.plugins');

/**
 * @class Deluge.plugins.YaRSS2Plugin
 * @extends Deluge.Plugin
 */
Deluge.plugins.YaRSS2Plugin = Ext.extend(Deluge.Plugin, {
    name: 'YaRSS2',

    onDisable: function() {
        deluge.preferences.removePage(this.prefsPage);
    },

    onEnable: function() {
        this.prefsPage = deluge.preferences.addPage(
            new Deluge.ux.preferences.YaRSS2Page()
        );
    },
});

Deluge.registerPlugin('YaRSS2', Deluge.plugins.YaRSS2Plugin);
