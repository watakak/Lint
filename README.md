# Lint
Lint - an Hybrid-Programing Language writed with Python which is based on C++, so the source code of .lint file will compile into C++ code.

# Examples:

### main.lint
```python
password: 120

loop code for 999 {
    if code == password {
        log('The password was: <code>')
        stop
    }
    log(code)
}
```

## converts into..

### main.cpp:
```cpp
#include <iostream>
using namespace std;
int main() {
    int password = 120;
    
    for (int code = 0; code < 999; code++) {
    if (code == password) {
    cout << "The password was: " << code << "" << endl;
    break;
    }
    cout << code << endl;
    }
    return 0;
}

```

or optimized version (compress size by 40%, working a little faster)

### main.cpp (optimized):
```cpp
#include <iostream>
 using namespace std;int main(){int password=120;for(int code=0;code<999;code++){if(code == password){cout<<"The password was: "<<code<<endl;break;}cout<<code<<endl;}return 0;}
```
