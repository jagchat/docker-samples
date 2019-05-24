#!/usr/bin/env node

var amqp = require('amqplib/callback_api');

amqp.connect('amqp://pd-docker-dev.psfy.personifycorp.com:5672', function(err, conn) {
  conn.createChannel(function(err, ch) {
    ////uses round robin method for the consumers
	////-a consumer gets one turn for one publish
	////-second publish goes to second consumer (waiting meanwhile), similarly third
	////-once a round is finished covering all consumers (for each/one publish at a time), the next publish goes to first consumer
	//var q = 'hello';
    //ch.assertQueue(q, {durable: false});
    //console.log(" [*] Waiting for messages in %s. To exit press CTRL+C", q);
    //ch.consume(q, function(msg) {
    //  console.log(" [x] Received %s", msg.content.toString());
    //}, {noAck: true});
	
	
	//uses fanout method (all subscribers would receive same message at once)
	var exchange = 'global';
    ch.assertExchange(exchange, 'fanout', {durable: false});
    ch.assertQueue('', {exclusive: true }, function(error2, q) {
		if (error2) {
			throw error2;
		}
		console.log(" [*] Waiting for messages in %s. To exit press CTRL+C", q.queue);
		ch.bindQueue(q.queue, exchange, '');

		ch.consume(q.queue, function(msg) {
			if(msg.content) {
				console.log(" [x] Received %s", msg.content.toString());
			}
		}, 
		{noAck: true});	
	});
	
  });
});
