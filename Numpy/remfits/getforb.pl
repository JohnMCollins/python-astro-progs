#! /usr/bin/perl

use dbops;
use remdefaults;
use Getopt::Long;

sub wgetfile ($) {
    my $fname = shift;
    my $fitsfile = "";
    my $next;
    open(WG, "wget -q -O - $fname|") or die "Cannot create pipe";
    while (sysread(WG, $next, 4096) > 0)  {
	   $fitsfile .=	$next;
    }
    close WG;
    if (length($fitsfile) < 10000 || (substr $fitsfile, 0, 6) eq '<html>')  {
        print STDERR "Could not fetch $fname\n";
        return undef;
    }
    $fitsfile;
}

sub insertfits ($$) {
    my $dbase = shift;
    my $fitsfile = shift;
    my $sfh = $dbase->prepare("INSERT INTO fitsfile (fitsgz) VALUES (?)");
    $sfh->execute($fitsfile);
    $sfh = $dbase->prepare("SELECT LAST_INSERT_ID()");
    $sfh->execute;
    my $rr = $sfh->fetchrow_arrayref();
    $rr->[0];
}

my %pos = (z => "BL", r => "BR", g => "UR", i => "UL");
my @tbits = localtime;

my $year = $tbits[5] + 1900;
my $month = $tbits[4] - 1;
my $force;

if ($month < 0)  {
    $month = 11;
    $year--;
}
$month++;

my $dbasename = remdefaults::default_database;
GetOptions("database=s" => \$dbasename, "year=i" => \$year, "month=i" => \$month, "force", \$force);

my $dbase = dbops::opendb($dbasename) or die "Cannot open Database $dbasename";
my $sfh;
my $row;

unless  ($force)  {
    $sfh = $dbase->prepare("SELECT COUNT(*) FROM forbinf WHERE year=$year AND month=$month");
    $sfh->execute;
    $row = $sfh->fetchrow_arrayref;
    if ($row->[0] >= 8)  {
        print STDERR "Already got $month/$year\n";
        exit 10;
    }
}

$sfh = $dbase->prepare("DELETE FROM forbinf WHERE year=$year AND month=$month");
$sfh->execute;

my $padate = sprintf "%.4d%.2d", $year, $month;
for my $filt (qw/z i r g/)  {
    my $fname = "http://ross.iasfbo.inaf.it/RossDB/ROS2/masterflats/Master/master_flat_s_$padate" . "_" . $pos{$filt} . "_" . $filt . "_1s_norm.fits.gz";
    my $fitsfile = wgetfile $fname;
    next unless defined $fitsfile;
    my $ind = insertfits $dbase, $fitsfile;
    my $sfh = $dbase->prepare("INSERT INTO forbinf (year,month,filter,typ,fitsind) VALUES ($year,$month,'$filt','flat',$ind)");
    $sfh->execute;
    $fname = "http://ross.iasfbo.inaf.it/RossDB/ROS2/masterbias/Master/master_bias_s_$padate" . "_" . $pos{$filt} . "_" . $filt . ".fits.gz";
    $fitsfile = wgetfile $fname;
    next unless defined $fitsfile;
    $ind = insertfits $dbase, $fitsfile;
    $sfh = $dbase->prepare("INSERT INTO forbinf (year,month,filter,typ,fitsind) VALUES ($year,$month,'$filt','bias',$ind)");
    $sfh->execute;
}
exit 0;
