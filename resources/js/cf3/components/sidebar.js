define(['react', 'underscore', 'components/glyphicon'], function (React, _, Glyphicon) {

    var SidebarListItem = React.createClass({
        handleClick: function(e) {
            e.preventDefault();
            this.props.onClick(this.props.id);
        },
        render: function() {
            return React.DOM.li(
                {className: this.props.active ? 'active' : ''}, 
                React.DOM.a(
                    {
                        href: url_root + this.props.id,
                        onClick: this.handleClick
                    },
                    Glyphicon({name: this.props.icon}), 
                    this.props.text
                )
            );
        }
    });

    var Sidebar = React.createClass({
        onClick: function(clicked) {
            this.props.onSelect(clicked);
        },
        render: function() {
            var items = _.map(this.props.items, function(item, id) {
                return SidebarListItem({
                    icon: item.icon, 
                    active: id == this.props.active,
                    onClick: this.onClick,
                    text: item.text,
                    id: id
                });
            }.bind(this));
            return React.DOM.div({id: 'sidebar'}, React.DOM.ul({}, items));
        }
    });

    return Sidebar;
});
