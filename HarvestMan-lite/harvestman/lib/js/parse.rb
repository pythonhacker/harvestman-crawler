require 'Parser'


filename = ARGV[0]
#filename = 'test.js'
jsfile = File.open(filename).read

jstree = parse(jsfile, filename)
#puts 'finished parsing'

def get_children (n)
        children = []
        attrs = [n.type, n.value, n.lineno, n.start, n.end, n.tokenizer, n.initializer,
                n.name, n.params, n.funDecls, n.varDecls, n.body, n.functionForm,
                n.assignOp, n.expression, n.condition, n.thenPart, n.elsePart,
                n.readOnly, n.isLoop, n.setup, n.postfix, n.update, n.exception,
                n.object, n.iterator, n.varDecl, n.label, n.target, n.tryBlock,
                n.catchClauses, n.varName, n.guard, n.block, n.discriminant, n.cases,
                n.defaultIndex, n.caseLabel, n.statements, n.statement]
        
        n.length.times do |i|
                children.push(n[i]) if n[i] != n and n[i].class == Node
        end
        
        attrs.length.times do |attr|
                children.push(attrs[attr]) if attrs[attr].class == Node and attrs[attr] != n
        end
        
        return children
end

def resolve_name (n)
        name = ""
        
        if n.type == $consts["DOT"]
                name = resolve_name(n[0]) + "." + resolve_name(n[1])
        else # INDENTIFIER
                name = n.value
        end
        
        return name
                
end

def get_functions (n, functions = nil)

        functions = {} unless functions

        function = nil
        name = nil

        if n.type == $consts["FUNCTION"] and n.name
                function = n
                name = n.name
        elsif n.type == $consts["ASSIGN"] && n[1].type == $consts["FUNCTION"] && !n[1].name
                function = n[1]
                name = resolve_name(n[0])
        end

        if function
                functions[name] = function
                #puts function.lineno.to_s + ": " + name
        end
        
        children = get_children(n)
        children.length.times do |i|
                get_functions(children[i], functions)
        end

        return functions
end

functions = get_functions(jstree)

if ARGV.length == 2
        jsfile[functions[ARGV[1]].start..functions[ARGV[1]].end]
else
        functions.each_key {|name| puts "Function => " + name}
end
