
var mongoose = require('mongoose');
var Schema = mongoose.Schema;

var MutateRequestSchema = new Schema({
    date: {type: Date, default: Date.now()},
    normie_asset_id: {type: String, required: true},
    mutation_asset_id: {type: String, required: true},
    from: {type: String, required: true, maxLength: 128}
});

module.exports = mongoose.model('mutate_request', MutateRequestSchema);
