//import platform.Foundation.NSURL
//import platform.darwin.NSObject

fun main() {
    val int_ = 0
    val void_ = Unit
    val string = "Hello world"
    val basic = Foo()
    val data = DataFoo(basic)
    val dataObject = DataObject
    val intList = listOf(1, 2, 3, 4)
    val basicList = listOf(basic)
    val dataList = listOf(data)
    val dataMap = mapOf("hello" to data)
//    val obj = NSObject()
//    val nsChild = NSObjectChild()

//    val nsBasic = basic as NSObject

    dataList.let {
        println(it)
    }

    dataList.forEach { help ->
        println()
    }

	basic.bar()

    println()
}

//class NSObjectChild: NSObject() {
//    val foo = Foo()
//}

class Foo {
    val int: Int = -8

    val boolean: Boolean = false

    val string: String = "Hello world"

    val double: Double = 3.14

    val float: Float = 1.23f

    fun bar() {
		val something = "no"

		fun what() {
			val hello = "yo"
			println()
		}

        something.let {
            println()
        }
		what()
        println()
    }
}

data class DataFoo(
    val foo: Foo
)

data object DataObject {
    val child = DataFoo(Foo())
}
