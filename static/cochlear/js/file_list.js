$(function(){
	function SortRowArray(array,reverse){
		//Helper function to apply alphanumeric sorting on an array of row elements
		//First step is to extract the inner html values
		var pureArray = []
		var arrayDict = {}
		for(var i=0;i<array.length;i++){
			pureArray.push(array[i].innerHTML)
			arrayDict[array[i].innerHTML] = array[i]
		}
		//Now we sort the pure function
		pureArray.alphanumSort();
		if(reverse) pureArray.reverse();//If we want descending
		//Now we match the original array order with the pure one
		for(i=0;i<array.length;i++){
			array[i] = arrayDict[pureArray[i]]
		}
	}

	//When any header is clicked, sort its list
	var tableHeaders = $('.item-table-header');
	for(var i=0;i<tableHeaders.length;i++){
		var header = $(tableHeaders[i]);//This is the table header (the part that doesn't move as it scrolls)
		//Grab the individual headers that we can click on 
		var buttonArray = header.find("th");
		for(var j=0;j<buttonArray.length;j++){
			var button = $(buttonArray[j]);
			button.on("click",function(evt){//If any of these are clicked
				var idName = $(evt.target).attr("id");//Which header button is this?
				var className = idName.replace("headbutton","items");//Get the class name of all of its items
				var itemArray = $('.'+className);//Now we have a list of all the items to sort
				var tBody = $(itemArray[0]).parent().parent();
				//Sort the itemArray
				if($(evt.target).attr("sorted") == "desc"){
					$(evt.target).attr("sorted","asc");
					//Sort ascendlingly
					SortRowArray(itemArray);

				} else {
					//Sort descendingly 
					$(evt.target).attr("sorted","desc");
					SortRowArray(itemArray,true);
				}
				
				
				//Produce the new html
				var newBodyHTML = "";
				for(var k=0;k<itemArray.length;k++){
					var row = $(itemArray[k]).parent();
					newBodyHTML += "<tr>"
						newBodyHTML +=  row.html()
					newBodyHTML += "</tr>"
				}
				tBody.html(newBodyHTML);
			})
		}
		
	}
})