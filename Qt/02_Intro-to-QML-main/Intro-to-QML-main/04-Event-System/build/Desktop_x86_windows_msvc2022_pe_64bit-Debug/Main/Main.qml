import QtQuick

Window {
    id: window
    width: 640
    height: 360
    visible: true
    title: qsTr("Hello World")
    color: "#00414A"

    component SquareButton: Rectangle {
        id: root

        // These are the signal declarations.
        signal activated(xPosition:real, yPosition:real)
        signal deactivated

        property int side: 100
        width: side; height: side
        color: "#2CDE85"

        MouseArea {
            id : mousepointer
            anchors.fill: parent
            hoverEnabled : true
            // This will emit the signal when the mouse is released.
            onReleased: root.deactivated()
            /*
            This will emit the signal when the mouse is pressed.
            The mouse position is passed as an argument.
            */
            property real xvalue : mousepointer.mouseX
            property real yvalue : mousepointer.mouseY
            //onPositionChanged: (mouse)=> (xvalue = mouse.x , yvalue = mouse.y)
            onPressed: (mouse)=> root.activated(mouse.x, mouse.y)
        }

        Rectangle{

            width : 5
            height : 5
            color : "#255E85"

            x : mousepointer.xvalue
            y : mousepointer.yvalue

        }
    }

    SquareButton{
        // This will print "Deactivated" when the mouse is released.
        onDeactivated: console.log("Deactivated")
        // This will print "Activated at: <xPosition> <yPosition>" when the mouse is pressed.
        onActivated: (xPosition, yPosition) =>
            console.log("Activated at:", xPosition, yPosition)
    }
}
