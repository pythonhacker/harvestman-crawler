Object.extend(Array.prototype, {
  intersect: function(array){
    return this.findAll( function(token){ return array.include(token) } );
  }
});
