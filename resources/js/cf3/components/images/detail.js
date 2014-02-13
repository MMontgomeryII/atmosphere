define(['react', 'models/application', 'collections/applications',
    'components/images/cards'], 
    function(React, App, AppCollection, Cards) {

    var ApplicationDetail = React.createClass({
        getInitialState: function() {
            return {application: null};
        },
        componentDidMount: function() {
            // TODO: This is what should happen if we have API support for it
            /*
            var app = new App({id: this.props.image_id});
            app.fetch({success: function(model) {
                this.setState({image: model});
            }.bind(this)});
            */
            // This is terrible.
            var apps = new AppCollection();
            apps.fetch({success: function(collection) {
                var app = collection.get(this.props.image_id);
                this.setState({application: app});
            }.bind(this)});
        },
        render: function() {
            var app = this.state.application;

            if (!app)
                return React.DOM.div({className: 'loading'});

            return React.DOM.div({}, 
                React.DOM.h1({}, app.get('name_or_id')),
                Cards.Rating({rating: app.get('rating')}),
                React.DOM.h2({}, "Description"),
                React.DOM.p({}, app.get('description')),
                React.DOM.h2({}, "Versions of this Image"));
        }
    });

    return ApplicationDetail;
});
