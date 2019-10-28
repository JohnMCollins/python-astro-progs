#! /usr/bin/perl

use dbcredentials;
use Getopt::Long;

sub max {
	my ($a, $b) =@_;
	$a > $b? $a: $b;
}

my $section;
my $host;
my $database;
my $user;
my $password;
my $login;
my $localport;
my $remoteport;
my $delsect;
my $listsects;

GetOptions("section=s" => \$section, "host=s" => \$host, "database=s" => \$database, "user=s" => \$user,
		"password=s" => \$password, "login=s" => \$login, "localport=i" => \$localport,
		"remoteport=i" => \$remoteport, "delsect" => \$delsect, "list" => \$listsects) or die "Invalid options";

die "No section given" unless $section or $listsects;

$dbc = dbcredentials->new;

if ($listsects)  {
	my @Slist;
	my $maxn = 4;
    my $maxh = 4;
    my $maxu = 4;
    my $maxd = 8;
    if (defined $dbc->{DEFAULT}) {
    	my $dh = $dbc->{DEFAULT};
        push @Slist, ['DEFAULT', $dh];
        $maxn = 7;
        $maxh = max($maxh, length($dh->{host}));
        $maxu = max($maxu, length($dh->{user}));
        $maxd = max($maxd, length($dh->{database}));
    }

    for my $k (sort keys %$dbc) {
    	next if $k eq 'DEFAULT';
    	my $dh = $dbc->{$k};
    	push @Slist, [$k, $dh];
    	$maxn = max($maxn, length($k));
    	$maxh = max($maxh, length($dh->{host}));
        $maxu = max($maxu, length($dh->{user}));
        $maxd = max($maxd, length($dh->{database}));
    }
    
    printf "%-${maxn}s %-${maxh}s %-${maxd}s %-${maxu}s Remote connection\n", "Name", "Host", "Database", "User";
    
    for my $hp (@Slist) {
    	my ($k, $dh) = @$hp;
    	printf "%-${maxn}s %-${maxh}s %-${maxd}s", $k, $dh->{host}, $dh->{database};
        if ($dh->{localport}) {
        	printf " %-${maxu}s %d => %s", $dh->{user}, $dh->{localport}, $dh->{login};
        	print ":", $dh->{remoteport} if defined $dh->{remoteport};
        }
        else {
        	print " ", $dh->{user};
        }
        print "\n";
    }
    exit 0;
}

if  ($delsect)  {
	$dbc->delcreds($section);
}
else  {
	if (defined $dbc->{$section})  {
		die "Must give local port with ssh login" if !defined $dbc->{$section}->{login} && $login && !$localport;
	}
	else  {
		die "No host given" unless $host;
		die "No database given" unless $database;
		die "No user name given" unless $user;
		die "No password given" unless $password;
		die "No local port given" if $login && !$localport;
	}
	$dbc->{$section}->{host} = $host if $host;
	$dbc->{$section}->{database} = $database if $database;
	$dbc->{$section}->{user} = $user if $user;
	$dbc->{$section}->{login} = $login if $login;
	$dbc->{$section}->{password} = $password if $password;
	$dbc->{$section}->{localport} = $localport if $localport;
	$dbc->{$section}->{remoteport} = $remoteport if $remoteport;
}

$dbc->write;
