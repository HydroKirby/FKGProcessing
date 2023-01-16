const { mwn } = require('mwn');
//const fs = require(‘fs’);
const editlist = require('./editlist.json');
const editlistkey = Object.keys(editlist);
const readline = require('readline').createInterface({
  input: process.stdin,
  output: process.stdout
});

const bot = new mwn({
    apiUrl: 'https://flowerknight.fandom.com/api.php',
    username: '',
    password: '',
    userAgent: 'mwn/1.11.4',
    defaultParams: {
        assert: 'user' //ensure we're logged in
    }
});

function editBot(title, content, summary_text='Automatic update by bot.', minor_edit=true) {
	bot.edit(title, (rev) => {
		return {
			text: content,
			summary: summary_text,
			minor: minor_edit
		};
	});
}

function readBot(pageTitle) {
    bot.read(pageTitle).then((response) => {
		console.log(response['revisions'][0]['content']);
	});
}

function BatchEdit() {
	index = 0;
	
	editlistkey.forEach(function(entryKey) {
		setTimeout(function(){
			editBot(entryKey, editlist[entryKey]["content"]);
		}, 3000 * (index));
		index++
		console.log(`Edited ${entryKey}`);
	});
	
	setTimeout(function(){
		readline.question("\nPress Enter to exit...\n", name => {
			readline.close();
		});
	}, 3000 * (index));
}

BatchEdit()
