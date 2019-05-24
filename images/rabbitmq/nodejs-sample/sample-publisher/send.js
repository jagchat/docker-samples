#!/usr/bin/env node

var amqp = require('amqplib/callback_api');

amqp.connect('amqp://pd-docker-dev.psfy.personifycorp.com:5672', function(err, conn) {
  conn.createChannel(function(err, ch) {
    ////uses round robin method for the consumers
	////-a consumer gets one turn for one publish
	////-second publish goes to second consumer (waiting meanwhile), similarly third
	////-once a round is finished covering all consumers (for each/one publish at a time), the next publish goes to first consumer
	//var q = 'hello';
    //var msg = 'Hello World!';
    //ch.assertQueue(q, {durable: false});
    //ch.sendToQueue(q, Buffer.from(msg));
    //console.log(" [x] Sent %s", msg);
	
	//uses fanout method (all subscribers would receive same message at once)
	var exchange = 'global'; //any name
	var msg = 'Hello World!';
	ch.assertExchange(exchange, 'fanout', {durable: false});
	ch.publish(exchange, '', Buffer.from(msg));
  });
  setTimeout(function() { conn.close(); process.exit(0) }, 500);
});
