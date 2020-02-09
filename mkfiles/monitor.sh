#!/bin/sh /etc/rc.common

START=99

start() {

        (
	WAN1=0
        WAN2=0

         while [ 1 ]; do
	    ip netns exec qrouter ping 8.8.8.8 -c 3 -W 1 > /dev/null
            if [ $? -eq 0 ]
            then 
                if [ $WAN1 -eq 0 ]
                then
                    ovs-ofctl -O OpenFlow15 -vwarn insert-buckets br-ex group_id=1,command_bucket_id=last,bucket=bucket_id:1,actions='resubmit(,1)',weight=1
                    WAN1=1
		fi
            else
                if [ $WAN1 -eq 1 ]
                then
                    ovs-ofctl -O OpenFlow15 remove-buckets br-ex group_id=1,command_bucket_id=1
                    WAN1=0
                fi
            fi

            ip netns exec qrouter ping 8.8.4.4 -c 3 -W 1 > /dev/null
            if [ $? -eq 0 ]
            then 
                if [ $WAN2 -eq 0 ]
                then
                    ovs-ofctl -O OpenFlow15 -vwarn insert-buckets br-ex group_id=1,command_bucket_id=last,bucket=bucket_id:2,actions='resubmit(,2)',weight=1
		    WAN2=1
                fi
            else
                if [ $WAN2 -eq 1 ]
                then
                    ovs-ofctl -O OpenFlow15 remove-buckets br-ex group_id=1,command_bucket_id=2
                    WAN2=0
                fi
            fi
        done) &
}
