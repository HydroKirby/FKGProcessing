const { mwn } = require('mwn');
//const fs = require(‘fs’);
const editlist = require('./editlist.json');
const editlistkey = Object.keys(editlist);

const bot = new mwn({
    apiUrl: 'https://flowerknight.fandom.com/api.php',
    username: '',
    password: '',
    userAgent: 'mwn/1.11.4',
    defaultParams: {
        assert: 'user' // ensure we're logged in
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
	editlistkey.forEach(function(entryKey) {
		editBot(entryKey, editlist[entryKey]["content"]);
	});
}

BatchEdit()