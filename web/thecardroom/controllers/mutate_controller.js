const { body, validationResult } = require('express-validator');

var MutateRequest = require('../models/MutateRequest');

//var async = require('async');

// Display mutate create form on GET.
exports.mutate_create_get = function(req, res, next) {
    res.render('mutate', { title: 'The Card Room | Mutate' });
};

// Handle Author create on POST.
exports.mutate_create_post = [
    // Validate and sanitize fields.
    body('from', 'From required').trim().isLength({min: 1}).escape(),
    body('normie_asset_id', 'Normie asset id required.').trim().isLength({ min: 1 }).escape(),
    body('mutation_asset_id', 'Mutation asset id required.').trim().isLength({ min: 1 }).escape(),
    
    // Process request after validation and sanitization.
    (req, res, next) => {
        const errors = validationResult(req);
        console.log('from: ' + req.body.from);
        var new_request = new MutateRequest(
            {
                normie_asset_id: req.body.normie_asset_id,
                mutation_asset_id: req.body.mutation_asset_id,
                from: req.body.from
            }
        );

        if (!errors.isEmpty()) {
            res.render('mutate', { title: 'The Card Room | Mutate', errors: errors.array() });
            return;
        }

        new_request.save(function (err) {
            if (err) {
                return next(err);
            }

            res.redirect('/mutate');
        })
    }
];
