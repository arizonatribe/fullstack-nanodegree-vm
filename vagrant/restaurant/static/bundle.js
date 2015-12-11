(function () {
    /**
     * Auto-hide any flash messages after 5 seconds
     */
    setTimeout(function() {
        $('#flash-messages').hide();
    }, 5000);

    /**
     * To be able to apply CSS styles to an `<input type=file >` is tricky, so we will make it invisible
     * and instead create a plain old button that will respond to being clicked by triggering the invisible
     * file upload button
     */
    $('#feaux-uploader').on('click', function() {
       $('#upload-file').trigger('click');
    });
    /**
     * The actual file upload button has an event handler bound to its change event to trigger the whole
     * process of reading in the file as an array buffer, converting to a base64 string, and placing that
     * string value into a hidden input field that will be parsed when the form is submitted
     */
    $('#upload-file').on('change', function(event) {
        updateFile(event.target.files[0]);
    });

    var reader = new FileReader();
    reader.onload = function(e) {
        updateFileContent(e.target.result, reader.pic);
    };

    /**
     * Simple check to make sure the picture is of the acceptable PNG type
     * @param {string} fileExtension A case insensitive string value representing the file type
     * @returns {string} If is an acceptable picture type, a non-blank (lowercase) string will be returned
     */
    function  isAcceptableFileType(fileExtension) {
        return /png/i.test(fileExtension) ? fileExtension.toLowerCase() : '';
    }
    /**
     * Take any base64 string value of the picture and place it into a hidden input field and also display
     * back to the user an image representation of the base64 string directly on the page
     * @param {object} pic An object containing the base64 encoded string corresponding to a PNG image
     */
    function setupPic(pic) {
        var picString,
            picElement = $('#item-picture');

        if (pic && pic.FileContent && isAcceptableFileType(pic.FileExtension)) {
            picString = 'data:image/' + pic.FileExtension + ';base64, ' + pic.FileContent;
            $('#hidden-pic').val(pic.FileContent);
            if (picElement.length) {
                picElement.attr('src', picString);
            } else {
                $('#image-placeholder').html('<img id="item-picture" class="item-picture" src="' + picString + '">');
            }
        }
    }
    /**
     * Processes a file from a JavaScript native `FileReader` load event target, checks to see it is an acceptable
     * image type, and then logs information about the file onto the reader object itself
     * @param {object} file A file object
     */
    function updateFile(file) {
        var name;

        if (file) {
            if (isAcceptableFileType(file.type.split('/')[1])) {
                name = file.name.split('.');
                if (name[0] && typeof name[0] === 'string') {
                    // Parse the file name
                    name.splice(name.length - 1, 1);

                    // Load the the file content as a base64 encoded string onto the file reader
                    reader.pic = {
                        FileName: name.join('.'),
                        FileExtension: file.type.split('/')[1]
                    };
                    reader.readAsArrayBuffer(file);
                }
            }
        }
    }
    /**
     * Responds to a file reader's read event by transforming
     * it into a base64 string and updating that onto the reader
     * object itself (if it has changed from the last time)
     * @param {*} buff The raw array buffer
     * @param {object} pic The `pic` object from the filed reader instance (we keep track of the imported picture on it)
     */
    function updateFileContent(buff, pic) {
        if (buff && pic) {
            var newBase64String = arrayBufferToBase64(buff);
            if (newBase64String !== pic.FileContent) {
                pic.FileContent = newBase64String;
                setupPic(pic);
            }
        }
    }
    /**
     * Simple conversion of an array buffer into a base64 encoded string
     * @param {*} buffer The raw array buffer
     * @returns {string} A converted bas64 string
     */
    function arrayBufferToBase64(buffer) {
        var binary = '',
            i = 0,
            bytes = new Uint8Array(buffer),
            len = bytes.byteLength;

        for (; i < len; i++) {
            binary += String.fromCharCode(bytes[i]);
        }

        return window.btoa(binary);
    }
})();