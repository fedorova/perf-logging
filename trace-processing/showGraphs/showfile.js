var numDivs = 0;

function createDivWithCloseButton(numericId) {

    var newDiv = document.createElement('div');
    newDiv.className = "float-right";
    newDiv.id = "div-close" + numericId;

    var newButton = document.createElement('a');
    newButton.href = "#";
    newButton.className = "close-icon";
    newButton.id = "close" + numericId;
    newButton.addEventListener('click', handleClose, false);

    newDiv.appendChild(newButton);
    console.log("appended " + newButton.id);
    return newDiv;
}

function createColorSelectorElement(numericId) {

    var newColorInput = document.createElement('input');
    newColorInput.type = "color";
    newColorInput.id = "color" + numDivs;
    newColorInput.className = "color-input"
    newColorInput.value = "#008000"; /* solid green */
    newColorInput.addEventListener('change',
				   handleColorChange, false);

    return newColorInput;
}

function createFileInputElement(numericId) {

    var newInput = document.createElement('input');
    newInput.type = "file";
    newInput.id = "file" + numericId;
    newInput.addEventListener('change',
			      handleFileSelect, false);

    return newInput;
}

function createNewOutputPane(numericId) {

    var newOutput = document.createElement('output');
    newOutput.id = "output" + numDivs;
    return newOutput;
}

function addDiv() {

    /* An increasing id for new divs and enclosing elements */
    numDivs++;

    var newDiv = document.createElement('div');
    newDiv.className = "float-border";
    newDiv.id = "div" + numDivs;

    /* Create the color selector element */
    var newColorInput = createColorSelectorElement(numDivs);
    newDiv.appendChild(newColorInput);

    /* Create the file input element */
    var newInput = createFileInputElement(numDivs);
    newDiv.appendChild(newInput);

    /* Add the close button */
    var newDivWithCloseButton = createDivWithCloseButton(numDivs);
    newDiv.appendChild(newDivWithCloseButton);

    /* Create the output pane for rendering the file */
    var newOutput = createNewOutputPane(numDivs)
    newDiv.appendChild(newOutput);

    var mainDiv = document.getElementById("main");
    mainDiv.appendChild(newDiv);
}

function getNumberFromStringId(theString) {

    return theString.replace( /^\D+/g, '');
}

function handleColorChange(evt) {

    console.log("Color changed: " + evt.target.value);
    console.log("Target id is: " + evt.target.id);

    var numericId = getNumberFromStringId(evt.target.id);
    /* Change the border of the parent div */
    var parentDiv = document.getElementById("div" + numericId);
    parentDiv.style.borderColor = evt.target.value;
}

function handleClose(evt) {

    console.log("Hit close: " + getNumberFromStringId(evt.target.id));

    var numericId = getNumberFromStringId(evt.target.id);
    var enclosingDiv = document.getElementById("div" + numericId);

    var mainDiv = document.getElementById("main");
    mainDiv.removeChild(enclosingDiv);
}

function handleFileSelect(evt) {

    var files = evt.target.files; // FileList object
    var f = files[0]; // We allow only one file
    var outputId = getNumberFromStringId(evt.target.id);

    if (!f.type.match('image.*')) {
	window.alert("Only image files can be selected");
	evt.target.value = "";
	return;
    }

    var reader = new FileReader();
    var outputPane = document.getElementById('output' + outputId);

    // Closure to capture the file information.
    reader.onload = (function(theFile) {
        return function(e) {
	    var output = [];
	    output.push('<p><strong>', escape(theFile.name), '</strong>')

	    outputPane.innerHTML = output.join('');

	    // Render image
	    var span = document.createElement('span');
	    /* The image size is the function of the file size */
	    imgSize = theFile.size / 300;
	    span.innerHTML = ['<p><img width="', imgSize, 'px" src="',
			      e.target.result,
			      '" title="', escape(theFile.name),
			      '"/>'].join('');
	    outputPane.insertBefore(span, null);
        };
    })(f);

    /* Read in the image file as a data URL. */
    reader.readAsDataURL(f);

    /*  Now add another div element for selecting the file, unless we are
     * replacing the file within a div with another file previously rendered.
     */
    if(outputId == numDivs)
	addDiv();
}


document.getElementById('file0').addEventListener('change',
						  handleFileSelect, false);

document.getElementById('color0').addEventListener('change',
						   handleColorChange, false);

document.getElementById('close0').addEventListener('click',
						   handleClose, false);

