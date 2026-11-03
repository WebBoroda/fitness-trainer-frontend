/* global wp, YuliiaBlockConfig */
(function (wp) {
    'use strict';
    if (!wp || !wp.blocks || !wp.blockEditor || !wp.components) return;
    const el = wp.element.createElement;
    const { registerBlockType } = wp.blocks;
    const { useBlockProps, MediaUpload, MediaUploadCheck } = wp.blockEditor;
    const { TextControl, TextareaControl, SelectControl, Button, PanelBody, Notice } = wp.components;
    const cfg = window.YuliiaBlockConfig || { schema: {}, themeUrl: '' };
    const sections = cfg.schema || {};
    const keys = Object.keys(sections);
    const options = keys.map(key => ({ label: sections[key].label, value: key }));

    registerBlockType('yuliia/section', {
        edit: function (props) {
            const section = props.attributes.section || 'mission';
            const data = sections[section] || {};
            const fields = props.attributes.fields || {};
            const update = (key, value) => {
                props.setAttributes({ fields: Object.assign({}, fields, { [key]: value }) });
            };
            const items = [];
            (data.texts || []).forEach((item, idx) => {
                const value = Object.prototype.hasOwnProperty.call(fields, item.key) ? fields[item.key] : item.default;
                const large = String(item.default).length > 90;
                const Component = large ? TextareaControl : TextControl;
                items.push(el(Component, {
                    key: 'text-' + item.key,
                    label: (idx + 1) + '. ' + item.label,
                    value: value,
                    onChange: v => update(item.key, v),
                    rows: large ? 3 : undefined
                }));
            });
            const imageFields = (data.images || []).map(item => {
                const url = fields[item.key] || (cfg.themeUrl + '/' + item.default);
                return el('div', { key: 'img-' + item.key, className: 'yf-editor-image' }, [
                    el('p', { key: 'label' }, item.label),
                    el('img', { key: 'preview', src: url, alt: '', loading: 'lazy' }),
                    el(MediaUploadCheck, { key: 'upload-check' },
                        el(MediaUpload, {
                            allowedTypes: ['image'],
                            onSelect: media => update(item.key, media.url || ''),
                            render: ({ open }) => el(Button, { variant: 'secondary', onClick: open }, 'Замінити у медіабібліотеці')
                        })
                    ),
                    el(Button, { key: 'reset', variant: 'tertiary', onClick: () => update(item.key, '') }, 'Повернути макетне фото')
                ]);
            });
            const linkFields = (data.links || []).map((item, index) =>
                el(TextControl, {
                    key: 'link-' + item.key,
                    label: 'Посилання ' + (index + 1) + ' (типово ' + item.default + ')',
                    value: Object.prototype.hasOwnProperty.call(fields, item.key) ? fields[item.key] : item.default,
                    onChange: v => update(item.key, v)
                })
            );
            return el('section', useBlockProps({ className: 'yf-editor-section' }), [
                el('div', { key: 'head', className: 'yf-editor-heading' }, [
                    el('strong', { key: 'title' }, 'YULIIA / ' + (data.label || section)),
                    el('p', { key: 'info' }, 'Динамічна секція. Вигляд на сайті відтворює затверджений макет.')
                ]),
                el(SelectControl, {
                    key: 'section',
                    label: 'Тип секції',
                    value: section,
                    options: options,
                    onChange: value => props.setAttributes({ section: value, fields: {} })
                }),
                el(Notice, { key: 'notice', status: 'info', isDismissible: false }, 'Зміни зберігаються у WordPress. Переглянь сторінку, щоб перевірити анімації й адаптивність.'),
                el(PanelBody, { key: 'texts', title: 'Заголовки, тексти та елементи', initialOpen: true }, items),
                el(PanelBody, { key: 'media', title: 'Фотографії (' + imageFields.length + ')', initialOpen: false }, imageFields),
                el(PanelBody, { key: 'links', title: 'Кнопки та посилання (' + linkFields.length + ')', initialOpen: false }, linkFields)
            ]);
        },
        save: function () { return null; }
    });
})(window.wp);
