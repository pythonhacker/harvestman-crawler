// derive.js: edward.frederick@revolution.com, 2/07
// By: Revolution Dev Team
// Questions/Resources: rails-trunk@revolution.com, revolutiononrails.blogspot.com, www.edwardfrederick.com

Object.chain = function(dest,source){                   
  for (var property in source) {
          var chainprop = '__' + property + '_chain';
                if (!property.match(/__.*_chain$/)){
                        if (!dest[chainprop]){
                                dest[chainprop] = new Array();
                        }
                        if (dest[property]){
                                dest[chainprop].unshift(dest[property]);
                        }
                        if (source[chainprop]){
                                dest[chainprop] = source[chainprop].concat(dest[chainprop]);
                        }
                        dest[property] = source[property];
                }
  }
  return dest;  
}

Object.extend(Class, {
  derive: function(superclass, body){
                var ctr = Class.create();               
                if (superclass){
                        ctr.superclass = superclass;
                        Object.chain(ctr.prototype,superclass.prototype);                       
                        Object.chain(ctr,superclass);
                        if (superclass.inherited)
                          superclass.inherited(ctr);
                }               
                if (body){
                        if (body.self)
                                Object.chain(ctr,body.self);            
                        body.self = undefined;
                        Object.chain(ctr.prototype,body);
                }
                Object.extend(ctr,Class._deriveClassExtensions);
                Object.extend(ctr.prototype,Class._deriveInstanceExtensions);           
                return ctr;                     
  },
        _deriveClassExtensions: {       
                include: function(mixin){
                        if (!mixin._mixin)
                                throw "Can only include a mixin!";                              
                        Object.chain(this.prototype,mixin.methods);
                        if (mixin.self && mixin.self.included)
                                mixin.self.included(this);
                },
                extend: function(mixin){
                        if (!mixin._mixin)
                                throw "Can only extend a mixin!";
                        Object.chain(this,mixin.methods);
                        if (mixin.self && mixin.self.extended)
                                mixin.self.extended(this);
                }
        },
        _deriveInstanceExtensions: {
                sup: function(method){
                        var currentLinkVar = '__' + method + '_current_chain_link';
                        var chainVar = '__' + method + '_chain';

                        if (!this[currentLinkVar])
                                this[currentLinkVar] = 0;
                        if (this[currentLinkVar] && this[currentLinkVar] >= this[chainVar].size())
                                throw "NoPreviousMethod: " + method;    
        
                        var mine = this[chainVar][this[currentLinkVar]];
                        this[currentLinkVar]++;
                        
                        var shiftedArguments = new Array();
                        for (var i = 1; i < arguments.length; i++)
                                shiftedArguments.push(arguments[i]);
                                
                        var result = mine.apply(this,shiftedArguments);
                        this[currentLinkVar] = undefined;
                        return result;
                }
        }       
});

/* Can also mix things in horizontally, as the derive heirarchies are 
         intended to be singly-rooted */
var Mixin = {
        create: function(object){
                var mixin = {};
                var methods = Object.extend({},object);
                Object.extend(mixin,{
                        self: methods.self,
                        _mixin: true,
                        methods: methods
                });
                mixin.methods.self = undefined;
                Object.extend(mixin, Mixin._classMethods);
                return mixin;
        },
        _classMethods: {
                included: Prototype.emptyFunction,
                extended: Prototype.emptyFunction
        }
}


/* Singleton mixin provided as an example (albeit a useful one) */
var Singleton = Mixin.create({
        instance: function(){
                if (this._instance)
                        return this._instance;
                else
                        return this._instance = new this(arguments);
        },
        self: {
                included: function(klass){
                        // nothing here, but could be
                },
                extended: function(klass){
                        // nothing here, but could be
                }
        }
});
