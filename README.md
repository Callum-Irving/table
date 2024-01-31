# Table

A programming language that aims to have:
- The elegance of Java
- The speed of Python
- The ease-of-use of assembly


## TODO

- [ ] Parse generics
- [ ] Parse traits
- [ ] Parse structs
- [ ] Parse pointer types
- [ ] Add arrays
    - Should array types be `int[]` or `[int]`?
- [ ] Add tuples?
- [ ] Submodules?
    - Like Rust's mod


## Syntax Example

```
import "std.str.String";
import "std.io";
import "std.range";

# ExampleStruct implements interface ToString
struct ExampleStruct : ToString {
    x: int,
    y: int,

    fun add5(self: *ExampleStruct) {
        self.x += 5;
        self.y += 5;
    }

    fun to_string(self: *ExampleStruct): String {
        let string = String.new();
        string.concat(x); # int already implements ToString
        string.concat(", ");
        string.concat(y);
        return string;
    }
}

# Generics:
fun print_twice[T: ToString](item: *T) {
    io.println(item);
    io.println(item);
}

fun main() {
    # This is a comment
    const number: int = 5;
    io.println(number);

    let ex: ExampleStruct = ExampleStruct { x: 5, y: -5 };
    ex.add5();

    # Can print ex since it implements ToString
    io.println(*ex);

    # For loop:
    for x : range.new(0, 5) {
        # Can iterate through anything that implements the "Iter" interface
    }
}
```
