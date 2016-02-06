python-basketball-rss
=============
<body>
  <p>RSS feed for each NBA team providing game recaps from ESPN. Updated daily.</p>
  
  <h3>Recommended Use of the Feed</h3>
  <p>I wrote this application to be used with <a href="http://rainmeter.net">Rainmeter</a> which can be downloaded <a href="https://github.com/rainmeter/rainmeter/releases/download/v3.3.0.2519/Rainmeter-3.3.exe">here</a>. An example of how the feed will look: </p>
  <img src="http://i.imgur.com/bYFszSQ.png"/>
  
  <h3>Rainmeter Setup</h3>
  <p>1. Install Rainmeter from the link above.</p>
  <p>2. It should load several skins on your screen. Right click on each and unload all of them.</p>
  <p>3. Download <a href="http://www.deviantart.com/download/314413439/illustro_extended___1_3_1_by_harleygorillason-d576yyn.rmskin?token=5e05fa012c6856eb6a03a4441705c9d79b016648&ts=1411948780"> Illustro Extended</a>. The download button is on the right side of the page.</p>
  <p>4. Open the file and click install.</p>
  <p>5. Right click the Rainmeter notification icon. The icon may be hidden. Click on Manage Rainmeter. You should see this:</p>
  <img src="http://i.imgur.com/xfBaTVZ.png">
  <p>6. Click on the arrow next to illustro Extended - Release and do the same for Feeds. Right click on UniNews.ini and click load. The skin should now be on your screen. You can drag it where you would like to place it.</p>
  <p>7. Download the UniNews.ini file from the project and replace the UniNews.ini at the following path: C:\Users\Name\Documents\Rainmeter\Skins\illustro Extended - Release\Feeds/</p>
  <p>8. Replace line 21 with:<p/>
  <code>UniNewsFeedURL=https://raw.githubusercontent.com/ak212/python-basketball-rss/master/feeds/DET/DET_feed.xml</code>
  <p>where DET is replaced by the three letter abbreviation for your team. To check what your team's abbreviation would be, check the feeds folder.</p>
  <strong>Thats it! You successfully set up Rainmeter to give you an RSS feed from your favorite team!</strong>
  
</body>
