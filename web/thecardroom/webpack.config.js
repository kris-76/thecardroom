const path = require('path');
const webpack = require('webpack');

module.exports = {
    entry: './public/javascripts/my_script.js',
    module: {
        rules: [
            {
                test: /\.(js|jsx)$/,
                exclude: /node_modules/,
                use: ['babel-loader'],
            }
        ],
    },
    resolve: {
        extensions: ['*', '.js', '.jsx'],
    },
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: 'my-first-webpack.bundle.js',
        publicPath: '/'
    },
    experiments: {
        syncWebAssembly: true,
    },
    plugins: [new webpack.HotModuleReplacementPlugin()],
    stats: {
        errorDetails: true
    },
    mode: 'production',    
};
