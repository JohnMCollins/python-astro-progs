#! /usr/bin/perl

use dbops;
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

GetOptions("year=i" => \$year, "month=i" => \$month, "force", \$force);

my $dbase = dbops::opendb('remfits') or die "Cannot open DB";
my $sfh;
my $row;

unless  ($force)  {
    $sfh = $dbase->prepare("SELECT COUNT(*) FROM forb WHERE year=$year AND month=$month");
    $sfh->execute;
    $row = $sfh->fetchrow_arrayref;
    if ($row->[0] >= 8)  {
        print STDERR "Already got $month/$year\n";
        exit 10;
    }
}

$sfh = $dbase->prepare("DELETE FROM forb  WHERE year=$year AND month=$month");
$sfh->execute;

my $padate = sprintf "%.4d%.2d", $year, $month;
for my $filt (qw/z i r g/)  {
    my $fname = "http://ross.iasfbo.inaf.it/RossDB/ROS2/masterflats/Master/master_flat_s_$padate" . "_" . $pos{$filt} . "_" . $filt . "_1s_norm.fits.gz";
    my $fitsfile = wgetfile $fname;
    next unless defined $fitsfile;
    $sfh = $dbase->prepare("INSERT INTO forb (year,month,filter,typ,fitsgz) VALUES ($year,$month,'$filt','flat',?)");
    $sfh->execute($fitsfile);
    $fname = "http://ross.iasfbo.inaf.it/RossDB/ROS2/masterbias/Master/master_bias_s_$padate" . "_" . $pos{$filt} . "_" . $filt . ".fits.gz";
    $fitsfile = wgetfile $fname;
    next unless defined $fitsfile;
    $sfh = $dbase->prepare("INSERT INTO forb (year,month,filter,typ,fitsgz) VALUES ($year,$month,'$filt','bias',?)");
    $sfh->execute($fitsfile);
}
exit 0;

$sfh = $dbase->prepare("SELECT ind,ffname,dithID FROM obs WHERE fitsgz IS NULL ORDER by date_obs");
$sfh->execute;

$root_url = 'http://ross.iasfbo.inaf.it';

while (my $row = $sfh->fetchrow_arrayref())  {
    my $ind = $row->[0];
    my $ffname = $row->[1];
    my $dithid = $row->[2];
    if ($dithid == 0)  {
        $ffname = 'Ross/' . $ffname;
    }
    else  {
        $ffname = 'Remir/' .  $ffname;
    }
    my $fitsfile = "";
    my $next;
    open(WG, "wget -q -O - $root_url/RossDB/fits_retrieve.php?ffile=/$ffname|") or die "Cannot create pipe";
    while (sysread(WG,$next,4096) > 0)  {
	   $fitsfile .=	$next;
    }
    close WG;
    if (length($fitsfile) < 10000 || (substr $fitsfile, 0, 6) eq '<html>')  {
        print "Could not fetch $ffname\n";
        next;
    }
    my $iq = $dbase->prepare("UPDATE obs SET fitsgz=? WHERE ind=$ind");
    $iq->execute($fitsfile);
}
