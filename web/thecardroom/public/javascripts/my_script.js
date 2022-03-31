// https://github.com/cardano-foundation/CIPs/tree/master/CIP-0030
// https://github.com/Emurgo/cip14-js
// https://github.com/Emurgo/cardano-serialization-lib

// https://stackoverflow.com/questions/27464168/how-to-include-scripts-located-inside-the-node-modules-folder
// https://cardano.stackexchange.com/questions/4112/nami-wallet-showing-getbalance-returning-a-nan

//https://webpack.js.org/guides/installation/

//import * as wasm from 'https://cdn.jsdelivr.net/npm/@emurgo/cardano-serialization-lib-asmjs@9.1.2/cardano_serialization_lib.min.js';

import {
    Address,
    BaseAddress,
    MultiAsset,
    Assets,
    ScriptHash,
    Costmdls,
    Language,
    CostModel,
    AssetName,
    TransactionUnspentOutput,
    TransactionUnspentOutputs,
    TransactionOutput,
    Value,
    TransactionBuilder,
    TransactionBuilderConfigBuilder,
    TransactionOutputBuilder,
    LinearFee,
    BigNum,
    BigInt,
    TransactionHash,
    TransactionInputs,
    TransactionInput,
    TransactionWitnessSet,
    Transaction,
    PlutusData,
    PlutusScripts,
    PlutusScript,
    PlutusList,
    Redeemers,
    Redeemer,
    RedeemerTag,
    Ed25519KeyHashes,
    ConstrPlutusData,
    ExUnits,
    Int,
    NetworkInfo,
    EnterpriseAddress,
    TransactionOutputs,
    hash_transaction,
    hash_script_data,
    hash_plutus_data,
    ScriptDataHash, Ed25519KeyHash, NativeScript, StakeCredential
} from "@emurgo/cardano-serialization-lib-asmjs"
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

    const balance = Value.from_bytes(Buffer.from(balance_cbor, "hex")).coin().to_str();
    console.log('balance = ' + balance);
}
