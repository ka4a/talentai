var PO = require('pofile');
const { exec } = require('child_process');

function main() {
  console.log('Loading current po file...');

  PO.load('./src/locales/en/messages.po', function(err, po) {
    if (err) {
      console.error(err);
      process.exit(1);
    }

    const beforeKeys = [];

    po.items.forEach(item => {
      beforeKeys.push(item.msgid);
    });

    console.log('Extracting strings file...');

    exec('npm run extract', (err, stdout, stderr) => {
      if (err) {
        console.error(err);
        process.exit(1);
      }

      console.log('Loading new po file...');
      PO.load('./src/locales/en/messages.po', function(err, po) {
        if (err) {
          console.error(err);
          process.exit(1);
        }

        const newKeys = [];

        po.items.forEach(item => {
          if (!beforeKeys.includes(item.msgid)) {
            newKeys.push(item.msgid);
          }
        });

        if (newKeys.length > 0) {
          console.error(
            'Found new keys! Run `npm run extract` and commit files\n',
            newKeys
          );
          process.exit(2);
        }
      });
    });
  });
}

main();
