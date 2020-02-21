#!/bin/sh /etc/rc.common

START=99
ADDRESS=8.8.8.8
BUCKETID=1
TABLEID=1
NAMESPACE=qrouter
BRIDGE=br-ex

start() {

        (
        STATUS=0

         while [ 1 ]; do
	        ip netns exec $NAMESPACE ping $ADDRESS -c 3 -W 1 > /dev/null
            if [ $? -eq 0 ]
            then 
                if [ $STATUS -eq 0 ]
                then
                    ovs-ofctl -O OpenFlow15 -vwarn insert-buckets $BRIDGE group_id=$BUCKETID,command_bucket_id=last,bucket=bucket_id:$BUCKETID,actions='resubmit(,$TABLEID)',weight=1
                    STATUS=1
		        fi
            else
                if [ $STATUS -eq 1 ]
                then
                    ovs-ofctl -O OpenFlow15 remove-buckets $BRIDGE group_id=$BUCKETID,command_bucket_id=$BUCKETID
                    STATUS=0
                fi
            fi
        done) &
}
