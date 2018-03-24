#! /usr/bin/perl

use dbops;
use strict;

my $dbase = dbops::opendb('remfits') or die "Cannot open DB";

my $sfh = $dbase->prepare("SELECT radeg,decdeg,object,dithID,filter,date_obs,mjdobs,exptime,fname,ffname,fitsgz FROM obs");
$sfh->execute;

while (my $row = $sfh->fetchrow_arrayref())  {
    
    my ($radeg, $decdeg, $object, $dith, $filter, $date_obs, $mjdate, $exptime, $fname, $ffname, $fitsgz) = @$row;
    
    my $ind = 0;
    if (length($fitsgz) != 0)  {
        my $ifh = $dbase->prepare("INSERT INTO fitsfile (fitsgz) VALUES (?)");
        $ifh->execute($fitsgz);
        $ifh = $dbase->prepare("SELECT LAST_INSERT_ID()");
        $ifh->execute;
        my $rr = $ifh->fetchrow_arrayref();
        $ind = $rr->[0];
    }
    
    my $qobj = $dbase->quote($object);
    my $qfilt = $dbase->quote($filter);
    my $qdo = $dbase->quote($date_obs);
    my $qfname = $dbase->quote($fname);
    my $qffname = $dbase->quote($ffname);
    my $iofb = $dbase->prepare("INSERT INTO obsinf (ind,radeg,decdeg,object,dithID,filter,date_obs,mjdobs,exptime,fname,ffname) VALUES ($ind,$radeg,$decdeg,$qobj,$dith,$qfilt,$qdo,$mjdate,$exptime,$qfname,$qffname)");
    $iofb->execute;
}
