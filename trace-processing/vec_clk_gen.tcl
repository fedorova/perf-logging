#!/usr/bin/tclsh

package require zlib

set num_threads 35
set min_lines 1917395
set max_lines 1926704
set dir ./
set outputlog $dir/vec_clk$min_lines-$max_lines.txt
set locknames {}
set trylock_status {}

proc getLockName {line} {
        set lock_name {}
        set line_split [split $line { }]
        set line_length [llength $line_split]

	if {$line_length < 5} {
		return 0
	} else {
        	for {set i 4} {$i < $line_length} {incr i} {
                	lappend lock_name [lindex $line_split $i]
        	}

        	set lock_name [join $lock_name "_"]
        	return $lock_name
	}
}

proc getEvent {line} {
	set lock [getLockName $line]
        if {[lindex $line 0] == "-->"} {
		if {$lock == 0} {
			set stored_event "Entering [lindex $line 1]"
		} else {
			set stored_event "Entering $lock[lindex $line 1]"
		}
        } else {
		if {$lock == 0} {
			set stored_event "Exiting [lindex $line 1]"
		} else {
			set stored_event "Exiting $lock[lindex $line 1]"
		}
        }
}

proc enteringLock {line} {
	set line_split [split $line { }]
	set direction [lindex $line_split 0]
	set function [lindex $line_split 1]

	if {[string match "<--" $direction]} {
		return 0
	} elseif {[string match "*lock*" $function] && ![string match "*unlock*" $function]} {
		return 1
	} else {
		return 0
	}	
}

proc exitingLock {line} {
	set line_split [split $line { }]
	set direction [lindex $line_split 0]
	set function [lindex $line_split 1]

	if {[string match "-->" $direction]} {
		return 0
	} elseif {[string match "*lock*" $function] && ![string match "*unlock*" $function]} {
		return 1
	} else {
		return 0
	}	
}

proc enteringTryLock {line} {
	set line_split [split $line { }]
	set direction [lindex $line_split 0]
	set function [lindex $line_split 1]

	if {[string match "<--" $direction]} {
		return 0
	} elseif {[string match "*trylock*" $function]} {
		return 1
	} else {
		return 0
	}	
}

proc exitingTryLock {line} {
	set line_split [split $line { }]
	set direction [lindex $line_split 0]
	set function [lindex $line_split 1]

	if {[string match "-->" $direction]} {
		return 0
	} elseif {[string match "*trylock*" $function]} {
		return 1
	} else {
		return 0
	}	
}

proc isSpinning {line} {
	set line_split [split $line { }]
	set direction [lindex $line_split 0]
	set function [lindex $line_split 1]

	if {[string match "*yield*" $function] && [string match "-->" $direction]} {
		return 1
	} else {
		return 0
	}	
}

proc unlocking {line} {
       set line_split [split $line { }]
       set direction [lindex $line_split 0]
       set function [lindex $line_split 1]

       if {[string match "<--" $direction]} {
		return 0
       } elseif {[string match "*unlock*" $function] || [string match "*release*" $function]} {
               return 1
       } else {
               return 0
       }
}

proc unlocked {line} {
       set line_split [split $line { }]
       set direction [lindex $line_split 0]
       set function [lindex $line_split 1]

       if {[string match "-->" $direction]} {
		return 0
       } elseif {[string match "*unlock*" $function] || [string match "*release*" $function]} {
               return 1
       } else {
               return 0
       }
}

proc formatVC {host vc} {
        set clk {}

        for {set i 0} {$i < [llength $vc]} {incr i} {
                if {[lindex $vc $i] > 0} {
                        lappend clk "\"thread$i\":[lindex $vc $i]"
                }
        }
        set clk_str [lindex $clk 0]
        set clk_str "{$clk_str"
        set clk [lreplace $clk 0 0 $clk_str]

        set last_clk [llength $clk]
        set last_clk [expr $last_clk - 1]
        set clk_str [lindex $clk $last_clk]
        append clk_str }
        set clk [lreplace $clk $last_clk $last_clk $clk_str]
        set clk [join $clk ", "]
#       puts $clk
        set  clk "$host $clk"
#       puts $clk

#        set clk [string replace $clk  0 0 ""]
#        set last_bracket [string length $clk]
#        set last_bracket [expr $last_bracket - 2]
#        set clk [string replace $clk $last_bracket $last_bracket ""]
#        set clk "$host $clk"
        return $clk

}

proc max {num0 num1} {
	if {$num0 > $num1} {
		return $num0
	} elseif {$num1 > $num0} {
		return $num1
	} else {
		return $num0
	}
}

for {set i 0} {$i < $num_threads} {incr i} {
	set threadlog $dir/thread${i}.txt
	if {[file exists $threadlog]} {
		file delete $threadlog
	}
	set f [open $threadlog w]
	close $f
}

for {set i 0} {$i < $num_threads} {incr i} {
	set stored_lines($i) {}
	lappend trylock_status 0
        for {set j 0} {$j < $num_threads} {incr j} {
                lappend vc($i) 0
        }
}

if {[file exists temp.txt]} {
	file delete temp.txt
}

if {[file exists temp.txt.gz]} {
	file delete temp.txt.gz
}

if {[file exists $outputlog]} {
	file delete $outputlog
}

set fd_temp [open temp.txt w]

for {set i 0} {$i < $num_threads} {incr i} {
        set count 0
	set logfile $dir/log.txt.$i.gz
        set fd [open $logfile]
        zlib push gunzip $fd

        while {[gets $fd line] >= 0} {
               incr count
#
#		if {$count >= $max_lines} {
#			break
#		} elseif {$count >= $min_lines} {
#        		set match [regexp {(\-\-\>|\<\-\-)(\s+)(__\w+)(\s+)(\d+)(\s+)(\d+)} $line]
#        		if {$match} {
#             			puts $fd_temp $line
#        		} else {
#                		puts "Uh oh, something is wrong with line $count of $logfile"
#        		}
#		}


        	set match [regexp {(\-\-\>|\<\-\-)(\s+)(__\w+)(\s+)(\d+)(\s+)(\d+)} $line]
        	if {$match} {
             		puts $fd_temp $line
        	} else {
			puts "Uh oh, something is wrong with line $count of $logfile"
		}
        }

        close $fd
}

close $fd_temp
exec less temp.txt | sort -t " " -k4n,4 -o temp.txt
exec gzip temp.txt

set temp_fd [open temp.txt.gz]
zlib push gunzip $temp_fd
set count 0

while {[gets $temp_fd line] >= 0} {
	incr count

	if {$count > $max_lines} {
		break;

	} elseif {$count >= $min_lines} {
		set t [lindex $line 2]
		set timestamp [lindex $line 3]
		set event [getEvent $line]
		set host "thread$t"

		if {[enteringLock $line]} {
			set threadlog $dir/thread$t.txt
			set f [open $threadlog a]

			set lockname [getLockName $line]

			### TEMPORARY: JUST CHECKING FOR FS LOCKS THIS WAY FOR NOW ####
#			set lock_func [lindex $line 1]
#			if {[string match "*_fs_*" $lock_func]} {
#				set lockname "fs"
#			} elseif {[string match "*fair*" $lock_func]} {
#			 	set lockname "fair"
#			} else {
#				set lockname [getLockName $line]
#			}
			###############################################################

			set lockIndex [lsearch $locknames $lockname]

			if {$lockIndex == -1} {
				lappend locknames $lockname
				set lockIndex [lsearch $locknames $lockname]
				set lk_vc($lockIndex) {}

				for {set i 0} {$i < $num_threads} {incr i} {
					lappend lk_vc($lockIndex) 0
				}
			}

			set own_clk [lindex $vc($t) $t]
			incr own_clk
			set vc($t) [lreplace $vc($t) $t $t $own_clk]
			set formattedVC [formatVC $host $vc($t)]

			#At this point, print vector clock to appropriate file
			set vc_header "$timestamp $event"
			puts $f $vc_header
			puts $f $formattedVC
			close $f

		
		} elseif {[unlocking $line]} {
			set threadlog $dir/thread$t.txt
			set f [open $threadlog a]
			
			set lockname [getLockName $line]

			### TEMPORARY: JUST CHECKING FOR FS LOCKS THIS WAY FOR NOW ####
#			set lock_func [lindex $line 1]
#			if {[string match "*_fs_*" $lock_func]} {
#				set lockname "fs"
#			} elseif {[string match "*fair*" $lock_func]} {
#				set lockname "fair"
#			} else {
#				set lockname [getLockName $line]
#			}
			###############################################################

			set lockIndex [lsearch $locknames $lockname]

			if {$lockIndex == -1} {
				puts "Uh oh, thread $t is unlocking $lockname at time $timestamp\ 
				without encountering it before"
				lappend locknames $lockname
				set lockIndex [lsearch $locknames $lockname]
				set lk_vc($lockIndex) {}

				for {set i 0} {$i < $num_threads} {incr i} {
					lappend lk_vc($lockIndex) 0
				}
			}

			if {[lindex $trylock_status $t] == 1 && [llength $stored_lines($t)] > 1} {
				puts "Uh oh, did not expect thread $t to have more than one stored line"	
			}

			if {[lindex $trylock_status $t] == 0 && [llength $stored_lines($t)] > 0} {
				puts "Uh oh, did not expect thread $t to havestored lines\
				when it is not acquiring any trylock."
			}

			if {[lindex $trylock_status $t] == 1 && [llength $stored_lines($t)] == 0} {
				puts "Uh oh, expected thread $t to have stored lines."
			}


			if {[lindex $trylock_status $t]} {
				for {set i 0} {$i < $num_threads} {incr i} {
					if {$i != $t} {
						set clk0 [lindex $vc($t) $i]
						set clk1 [lindex $lk_vc($lockIndex) $i]
						set new_clk [max $clk0 $clk1]
						set vc($t) [lreplace $vc($t) $i $i $new_clk]
					}
				}	
			}

			for {set i 0} {$i < [llength $stored_lines($t)]} {incr i} {
				set own_clk [lindex $vc($t) $t]
				incr own_clk
				set vc($t) [lreplace $vc($t) $t $t $own_clk]

				set stored_line [lindex $stored_lines($t) $i]
				set stored_timestamp [lindex $stored_line 3]
				set stored_formattedVC [formatVC $host $vc($t)]
				set stored_event [getEvent $stored_line]

				#At this point, print vector clock to appropriate file.
				set vc_header "$stored_timestamp $stored_event"
				puts $f $vc_header
				puts $f $stored_formattedVC
			}

			set own_clk [lindex $vc($t) $t]
			incr own_clk
			set vc($t) [lreplace $vc($t) $t $t $own_clk]
			set formattedVC [formatVC $host $vc($t)]

			#At this point, print vector clock to appropriate file
			set vc_header "$timestamp $event"
			puts $f $vc_header
			puts $f $formattedVC
			close $f

			if {[lindex $trylock_status $t]} {
				set stored_lines($t) {}
				set trylock_status [lreplace $trylock_status $t $t 0]
			}
			
			set lk_vc($lockIndex) $vc($t)	

		} elseif {[exitingLock $line]} {
			if {[exitingTryLock $line]} {
				lappend stored_lines($t) $line
				set trylock_status [lreplace $trylock_status $t $t 1]
			} else {
				set threadlog $dir/thread$t.txt
				set f [open $threadlog a]

				set lockname [getLockName $line]

				### TEMPORARY: JUST CHECKING FOR FS LOCKS THIS WAY FOR NOW ####
#				set lock_func [lindex $line 1]
#				if {[string match "*_fs_*" $lock_func]} {
#					set lockname "fs"
#				} elseif {[string match "*fair*" $lock_func]} {
#					set lockname "fair"
#				} else {
#					set lockname [getLockName $line]
#				}
				###############################################################

				set lockIndex [lsearch $locknames $lockname]

				if {$lockIndex == -1} {
					puts "Uh oh, thread $t is exiting $lockname at time $timestamp\
					before entering it"
					lappend locknames $lockname
					set lockIndex [lsearch $locknames $lockname]
					set lk_vc($lockIndex) {}

					for {set i 0} {$i < $num_threads} {incr i} {
						lappend lk_vc($lockIndex) 0
					}	
				}	

				for {set i 0} {$i < $num_threads} {incr i} {
					if {$i != $t} {
						set clk0 [lindex $vc($t) $i]
						set clk1 [lindex $lk_vc($lockIndex) $i]
						set new_clk [max $clk0 $clk1]
						set vc($t) [lreplace $vc($t) $i $i $new_clk]
					}
				}

				set own_clk [lindex $vc($t) $t]
				incr own_clk
				set vc($t) [lreplace $vc($t) $t $t $own_clk]
				set formattedVC [formatVC $host $vc($t)]

				#At this point, print vector clock to appropriate file
				set vc_header "$timestamp $event"
				puts $f $vc_header
				puts $f $formattedVC
				close $f

			}

		} elseif {[lindex $trylock_status $t] && [isSpinning $line]} {
			set threadlog $dir/thread$t.txt
			set f [open $threadlog a]
			
			if {[lindex $trylock_status $t] == 1 && [llength $stored_lines($t)] > 1} {
				puts "Uh oh, did not expect thread $t to have more than one stored line"	
			}

			for {set i 0} {$i < [llength $stored_lines($t)]} {incr i} {
				set own_clk [lindex $vc($t) $t]
				incr own_clk
				set vc($t) [lreplace $vc($t) $t $t $own_clk]

				set stored_line [lindex $stored_lines($t) $i]
				set stored_timestamp [lindex $stored_line 3]
				set stored_formattedVC [formatVC $host $vc($t)]
				set stored_event [getEvent $stored_line]

				#At this point, print vector clock to appropriate file.
				set vc_header "$stored_timestamp $stored_event"
				puts $f $vc_header
				puts $f $stored_formattedVC
			}

			set own_clk [lindex $vc($t) $t]
			incr own_clk
			set vc($t) [lreplace $vc($t) $t $t $own_clk]
			set formattedVC [formatVC $host $vc($t)]

			#At this point, print vector clock to appropriate file
			set vc_header "$timestamp $event"
			puts $f $vc_header
			puts $f $formattedVC
			close $f
			
			set stored_lines($t) {}
			set trylock_status [lreplace $trylock_status $t $t 0]

		} elseif {[lindex $trylock_status $t]} {
			set threadlog $dir/thread$t.txt
			set f [open $threadlog a]

			set lockname [getLockName $line]

			### TEMPORARY: JUST CHECKING FOR FS LOCKS THIS WAY FOR NOW ####
#			set lock_func [lindex $line 1]
#			if {[string match "*_fs_*" $lock_func]} {
#				set lockname "fs"
#			} elseif {[string match "*fair*" $lock_func]} {
#			 	set lockname "fair"
#			} else {
#				set lockname [getLockName $line]
#			}
			###############################################################

			set lockIndex [lsearch $locknames $lockname]

			if {$lockIndex == -1} {
				puts "Uh oh, thread $t is releasing $lockname before acquiring it at time $timestamp"
				lappend locknames $lockname
				set lockIndex [lsearch $locknames $lockname]
				set lk_vc($lockIndex) {}

				for {set i 0} {$i < $num_threads} {incr i} {
					lappend lk_vc($lockIndex) 0
				}	
			}	

			for {set i 0} {$i < $num_threads} {incr i} {
				if {$i != $t} {
					set clk0 [lindex $vc($t) $i]
					set clk1 [lindex $lk_vc($lockIndex) $i]
					set new_clk [max $clk0 $clk1]
					set vc($t) [lreplace $vc($t) $i $i $new_clk]
				}
			}

			if {[lindex $trylock_status $t] == 1 && [llength $stored_lines($t)] > 1} {
				puts "Uh oh, did not expect thread $t to have more than one stored line"	
			}

			for {set i 0} {$i < [llength $stored_lines($t)]} {incr i} {
				set own_clk [lindex $vc($t) $t]
				incr own_clk
				set vc($t) [lreplace $vc($t) $t $t $own_clk]

				set stored_line [lindex $stored_lines($t) $i]
				set stored_timestamp [lindex $stored_line 3]
				set stored_formattedVC [formatVC $host $vc($t)]
				set stored_event [getEvent $stored_line]

				#At this point, print vector clock to appropriate file.
				set vc_header "$stored_timestamp $stored_event"
				puts $f $vc_header
				puts $f $stored_formattedVC
			}


			set own_clk [lindex $vc($t) $t]
			incr own_clk
			set vc($t) [lreplace $vc($t) $t $t $own_clk]
			set formattedVC [formatVC $host $vc($t)]

			#At this point, print vector clock to appropriate file
			set vc_header "$timestamp $event"
			puts $f $vc_header
			puts $f $formattedVC
			close $f

			set stored_lines($t) {}
			set trylock_status [lreplace $trylock_status $t $t 0]

		} else {
			set threadlog $dir/thread$t.txt
			set f [open $threadlog a]

			set own_clk [lindex $vc($t) $t]
			incr own_clk
			set vc($t) [lreplace $vc($t) $t $t $own_clk]
			set formattedVC [formatVC $host $vc($t)]

			#At this point, print vector clock to appropriate file
			set vc_header "$timestamp $event"
			puts $f $vc_header
			puts $f $formattedVC
                	close $f
		}
	}
}

for {set t 0} {$t < $num_threads} {incr t} {
	set threadlog $dir/thread${t}.txt
	if {[llength $stored_lines($t)] > 0} {
		puts "Uh oh, thread $t has stored events..."
		set f [open $threadlog a]
		for {set i 0} {$i < [llength $stored_lines($t)]} {incr i} {
			set own_clk [lindex $vc($t) $t]
        		incr own_clk
        		set vc($t) [lreplace $vc($t) $t $t $own_clk]
			set host "thread$t"
			set stored_line [lindex $stored_lines($t) $i]
			set stored_timestamp [lindex $stored_line 3]
			set stored_formattedVC [formatVC $host $vc($t)]
			set stored_event [getEvent $stored_line]
			
			#At this point, print vector clock to appropriate file	
			set vc_header "$stored_timestamp $stored_event"
			puts $f $vc_header
			puts $f $stored_formattedVC
		}
		close $f
	}
}

close $temp_fd

if {[file exists $outputlog]} {
	file delete $outputlog
}

set f_output [open $outputlog w]
puts $f_output "(?<timestamp>(\\d*)) (?<event>.*)\\n(?<host>\\w*) (?<clock>.*)"
puts $f_output ""

for {set t 0} {$t < $num_threads} {incr t} {	
	set threadlog $dir/thread${t}.txt
	set hasMessages [file size $threadlog]

	if {$hasMessages} {
		set f [open $threadlog a]
		puts $f ""
		close $f
		set f [open $threadlog r]
		
		while {[gets $f line] >= 0} {
			puts $f_output $line
		}
		close $f
	}

	file delete $threadlog
}



close $f_output
