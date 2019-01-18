#! /usr/bin/perl

use dbcredentials;
use Getopt::Long;

my $section;
my $host;
my $database;
my $user;
my $password;
my $login;
my $localport;
my $remoteport;
my $delsect;

GetOptions("section=s" => \$section, "host=s" => \$host, "database=s" => \$database, "user=s" => \$user,
		"password=s" => \$password, "login=s" => \$login, "localport=i" => \$localport,
		"remoteport=i" => \$remoteport, "delsect" => \$delsect) or die "Invalid options";

die "No section given" unless $section;

$dbc = dbcredentials->new;

if  ($delsect)  {
	$dbc->delcreds($section);
}
else  {
	if (defined $dbc->{$section})  {
		die "Must give local port with sssh login" if !defined $dbc->{$section}->{login} && $login && !$localport;
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
