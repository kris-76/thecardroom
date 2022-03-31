class Loader 
{
    async load() 
    {
        if (this.loaded) 
            return;
  
        this.cslib = await import("@emurgo/cardano-serialization-lib-browser/");
        this.loaded = true;
    }

    get cardano_slib() {
        return this.cslib;
    }
}

export default new Loader();
