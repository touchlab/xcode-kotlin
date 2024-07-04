fun main() {
    val int = 0
    val void = Unit
    val string = "Hello world"
    val basic = Foo()
    val data = DataFoo(basic)
    val dataObject = DataObject
    val intList = listOf(1, 2, 3, 4)
    val basicList = listOf(basic)
    val dataList = listOf(data)
    val dataMap = mapOf("hello" to data)

    println()
}

class Foo {

}

data class DataFoo(
    val foo: Foo
)

data object DataObject {
    val child = DataFoo(Foo())
}
