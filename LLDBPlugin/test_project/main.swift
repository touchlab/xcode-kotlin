// import test_project
import S_h_A_r_e___D
import Foundation

MainKt.main()

print("Hello world!")

// test_project.Foo
// Test_projectFoo

let basic = Foo()
let data = DataFoo(foo: basic)
let dataObject = DataObject.shared
let basicList = [basic]
let dataList = [data]
let dataMap = ["hello": data]
let test = Test()
let testList = [test]

let nsBasic = basic as NSObject


struct Test {
    let x = Foo()
}
