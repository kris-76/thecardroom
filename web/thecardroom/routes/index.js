var express = require('express');
var router = express.Router();

/* GET home page. */
router.get('/', function(req, res, next) {
  res.render('index', { title: 'The Card Room' });
});

/* GET about page. */
router.get('/about', function(req, res, next) {
  res.render('about', { title: 'The Card Room | About' });
});

module.exports = router;
