function inorder(T) {
  if ((T.cargo  == '+') || (T.cargo  == '-') || (T.cargo  == '*') || (T.cargo  == '/'))
    return [].concat(inorder(T.left)).concat(T.cargo).concat(inorder(T.right));

  return new Array(T.cargo);
}

function preorder(T) {
  if ((T.cargo  == '+') || (T.cargo  == '-') || (T.cargo  == '*') || (T.cargo  == '/'))
    return [].concat(T.cargo).concat(preorder(T.left)).concat(preorder(T.right));

  return new Array(T.cargo);
}

function postorder(T) {
  if ((T.cargo  == '+') || (T.cargo  == '-') || (T.cargo  == '*') || (T.cargo  == '/'))
    return [].concat(postorder(T.left)).concat(postorder(T.right)).concat(T.cargo);

  return new Array(T.cargo);
}

function Tree(cargo, left, right) {
  this.cargo = cargo;
  this.left = left;
  this.right = right;
}

function split(s) {
  var r = [];
  var cur = '';
  for (var i = 0; i < s.length; ++i) {
    var c = s.charAt(i);
    if ((c == '+') || (c == '-') || (c == '*') || (c == '/') || (c == '(') || (c == ')')) {
      cur.replace(" ", "");
      if (cur.length > 0) {
        r.push(cur);
        cur = '';
      }
      r.push(c);
    } else {
      cur += c;
    }
  }
  if (cur.length > 0)
    r.push(cur);

  return r;
}

function getToken(tokens, expected) {
  if (tokens[0] == expected) {
    tokens.splice(0, 1);
    return true;
  }
    return false;
}

function getVar(tokens) {
  if (getToken(tokens, '(')) {
    var a = getSum(tokens);
    getToken(tokens, ')');

    return a;
  } else {
    var aux = tokens[0];
    tokens.splice(0, 1);

    return new Tree(aux, undefined, undefined);
  }
}

function getProduct(tokens) {
  var a = getVar(tokens);

  if (getToken(tokens, '*')) {
    var b = getProduct(tokens);

    return new Tree('*', a, b);
  } else if (getToken(tokens, '/')) {
    var b = getProduct(tokens);

    return new Tree('/', a, b);
  }

  return a;
}

function getSum(tokens) {
  var a = getProduct(tokens);

  if (getToken(tokens, '+')) {
    var b = getSum(tokens);

    return new Tree('+', a, b);
  } else if (getToken(tokens, '-')) {
    var b = getSum(tokens);

    return new Tree('-', a, b);
  }

  return a;
}

function evalExp(s) {
  var tokens = split(s);

  //alert(tokens);

  return t = getSum(tokens);
}
