const puppeteer = require('puppeteer');
const fs = require('fs');

(async () => {
  const browser = await puppeteer.launch({ headless: "new" }); // Use new headless mode
  const page = await browser.newPage();
  const url = 'https://selfh.st/icons';
  const outputFile = './icons_page.html'; // Relative to the script's execution dir

  console.log(`Loading page: ${url}`);
  try {
    await page.goto(url, {
      waitUntil: 'networkidle0', // Wait for network to be idle
      timeout: 60000 // Increase timeout to 60 seconds
    });

    console.log('Page loaded. Scrolling down to load all icons...');

    // Scroll down the page multiple times to ensure all content is loaded
    let previousHeight;
    let scrollAttempts = 0;
    const maxScrollAttempts = 20; // Limit attempts to prevent infinite loops

    while (scrollAttempts < maxScrollAttempts) {
      previousHeight = await page.evaluate('document.body.scrollHeight');
      await page.evaluate('window.scrollTo(0, document.body.scrollHeight)');
      // Wait for potential dynamic content loading
      await new Promise(resolve => setTimeout(resolve, 2000)); // Wait 2 seconds
      let newHeight = await page.evaluate('document.body.scrollHeight');
      if (newHeight === previousHeight) {
        console.log('Reached bottom of the page or no new content loaded.');
        break; // Exit loop if height doesn't change
      }
      scrollAttempts++;
      console.log(`Scrolled down attempt ${scrollAttempts}...`);
    }

    if (scrollAttempts === maxScrollAttempts) {
        console.warn('Max scroll attempts reached. Page might not be fully loaded.');
    }

    console.log('Getting page content...');
    const html = await page.content();

    console.log(`Saving page content to ${outputFile}`);
    fs.writeFileSync(outputFile, html);
    console.log('Page saved successfully.');

  } catch (error) {
    console.error('Error during page fetch or processing:', error);
  } finally {
    console.log('Closing browser...');
    await browser.close();
  }
})();