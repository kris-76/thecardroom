// https://github.com/cardano-foundation/CIPs/tree/master/CIP-0030
// https://github.com/Emurgo/cip14-js
// https://github.com/Emurgo/cardano-serialization-lib

// https://stackoverflow.com/questions/27464168/how-to-include-scripts-located-inside-the-node-modules-folder
// https://cardano.stackexchange.com/questions/4112/nami-wallet-showing-getbalance-returning-a-nan

//https://webpack.js.org/guides/installation/

import Loader from "./loader";
let Buffer = require('buffer/').Buffer

function is_installed() {
    if (!window.cardano) {
        return false;
    }

    if (!window.cardano.nami) {
        return false;
    }

    return true;
}

async function is_enabled() {
    return window.cardano.nami.isEnabled();
}

async function get_cardano_serialization_lib() {
    await Loader.load();
    return Loader.cardano_slib;
};

window.connect_to_wallet = async function connect_to_wallet() {
    if (!is_installed()) {
        console.log('Nami not installed');
        return false;
    }

    console.log('check enabled')
    var enabled = await is_enabled();
    console.log('enabled = ' + enabled)
    var nami_api = await window.cardano.nami.enable();
    const balance_cbor = await nami_api.getBalance()
    console.log('balance_cbor = ' + balance_cbor);

    const slib = await get_cardano_serialization_lib();

    const balance = slib.Value.from_bytes(Buffer.from(balance_cbor, "hex")).coin().to_str();
    console.log('balance = ' + balance);
}
